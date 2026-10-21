from data_model import ComparisonRequest
from typing import Self
from sklearn.base import RegressorMixin
from sklearn.base import BaseEstimator
from typing import Literal

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, SplineTransformer

from game_data_manager import GameDataManager
from game_utility import GameContext
from persistence import JsonlDB, PartyDB

from .fitness import UNSCALED_CATEGORIES, CatVec, party_to_category_vector

class Ranker(BaseEstimator, RegressorMixin):
    def __init__(self, weights: CatVec) -> None:
        self.weights = weights
    
    def fit(self, X, y = None) -> Self:
        return self
    
    def predict(self, X):
        vec_1d = np.atleast_1d(X).ravel()
        return np.dot(self.weights, vec_1d)

def team_features_pipeline() -> Pipeline:
    scaler_step = ColumnTransformer(
        transformers=[("scale_unbouded", MinMaxScaler(), UNSCALED_CATEGORIES)],
        remainder="passthrough",
    )
    steps = [
        ("scaler", scaler_step),
        ("splines", SplineTransformer(degree=1, n_knots=2, extrapolation="continue")),
    ]
    return Pipeline(steps)


def parse_data_from_db(db: PartyDB, game_context: GameContext) -> tuple[CatVec, CatVec]:
    mapper = game_context.mapper
    reqs = db.load_unique_records()

    teams_h, teams_l = [], []

    for request in reqs:
        # Skip unlabeled comparisons
        if request.better not in (1, 2):
            continue

        vec_1 = party_to_category_vector(
            mapper.to_party_domain(request.party_1), game_context
        )
        vec_2 = party_to_category_vector(
            mapper.to_party_domain(request.party_2), game_context
        )
        if request.better == 1:
            teams_h.append(vec_1)
            teams_l.append(vec_2)
        elif request.better == 2:
            teams_h.append(vec_2)
            teams_l.append(vec_1)

    if not teams_h:
        raise ValueError(
            "No labeled comparison records found. Records must have 'better' equal to 1 or 2."
        )

    teams_h_np = np.vstack(teams_h)
    teams_l_np = np.vstack(teams_l)
    return teams_h_np, teams_l_np


def create_diff_vectors(teams_h: CatVec, teams_l: CatVec) -> tuple[CatVec, CatVec]:
    if len(teams_h) != len(teams_l):
        raise ValueError("teams_h and teams_l must have identical lengths.")
    if len(teams_h) == 0:
        raise ValueError("Input teams arrays cannot be empty.")

    diff_pos = teams_h - teams_l
    diff_neg = teams_l - teams_h
    X = np.vstack([diff_pos, diff_neg])
    Y = np.concatenate([np.ones(len(diff_pos)), np.zeros(len(diff_neg))])
    return X, Y


def train_log_reg(
    X: CatVec,
    Y: CatVec,
    C: float = 1.0,
    penalty: Literal["l2", "l1", "elasticnet"] = "l2",
) -> LogisticRegression:
    """Trains a logistic regression model with fit_intercept=False for ranking symmetry."""
    model = LogisticRegression(
        C=C,
        penalty=penalty,
        solver="lbfgs",
        fit_intercept=False,
        random_state=42,
        max_iter=1000,
    )
    model.fit(X, Y)

    return model


def predict_team_score(
    model: LogisticRegression,
    team_catv: CatVec,
    preprocessor: Pipeline,
) -> float:
    vec2d = np.atleast_2d(team_catv)
    team_feat = preprocessor.transform(vec2d)
    vec_1d = np.atleast_1d(team_feat).ravel()
    return float(np.dot(model.coef_[0], vec_1d))


def run_training_pipeline() -> tuple[LogisticRegression, Pipeline]:
    """Runs data loading, preprocessing, model fitting, and metric printing."""
    print("=" * 70)
    print("DARKEST GENERATOR - ML RANKING MODEL TRAINING")
    print("=" * 70)

    game_context = GameContext(GameDataManager())
    gman = game_context.gman
    db = JsonlDB(gman)

    teams_h, teams_l = parse_data_from_db(db, game_context)
    
    print(f"Loaded {len(teams_h)} labeled pairwise comparisons from JSONL.")
        
    # 1. Train/Test split on the original paired comparisons
    h_train, h_test, l_train, l_test = train_test_split(
        teams_h, teams_l, test_size=0.25, random_state=42
    )

    # 2. Fit preprocessor strictly on training team vectors
    train_teams = np.vstack([h_train, l_train])
    feature_pipeline = team_features_pipeline()
    feature_pipeline.fit(train_teams)

    h_train_trans = feature_pipeline.transform(h_train)
    l_train_trans = feature_pipeline.transform(l_train)
    h_test_trans = feature_pipeline.transform(h_test)
    l_test_trans = feature_pipeline.transform(l_test)

    # 3. Build pairwise difference vectors
    X_train, Y_train = create_diff_vectors(h_train_trans, l_train_trans)
    X_test, Y_test = create_diff_vectors(h_test_trans, l_test_trans)
    print(
        f"Train shape: X={X_train.shape}, Test shape: X={X_test.shape} (augmented symmetric pairs)"
    )

    # 4. Train model
    model = train_log_reg(X_train, Y_train, C=1.0)

    scoring_model = Ranker(model.coef_[0])
    # 5. Predict & compute metrics on test set
    Y_pred = model.predict(X_test)
    Y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(Y_test, Y_pred)
    prec = precision_score(Y_test, Y_pred, zero_division=0)
    rec = recall_score(Y_test, Y_pred, zero_division=0)
    f1 = f1_score(Y_test, Y_pred, zero_division=0)
    bce = log_loss(Y_test, Y_prob)

    try:
        auc = roc_auc_score(Y_test, Y_prob)
    except ValueError:
        auc = float("nan")

    scores_h = np.array(
        [predict_team_score(model, vec, feature_pipeline) for vec in h_test]
    )
    scores_l = np.array(
        [predict_team_score(model, vec, feature_pipeline) for vec in l_test]
    )
    pairwise_acc = np.mean(scores_h > scores_l)

    print("\n" + "-" * 70)
    print("MODEL PERFORMANCE METRICS (Test Set - Held Out)")
    print("-" * 70)
    print(f"  Classification Accuracy : {acc * 100:.2f}%")
    print(
        f"  Pairwise Ranking Accuracy: {pairwise_acc * 100:.2f}% (Winner Score > Loser Score)"
    )
    print(f"  Precision               : {prec:.4f}")
    print(f"  Recall                  : {rec:.4f}")
    print(f"  F1-Score                : {f1:.4f}")
    print(f"  ROC AUC                 : {auc:.4f}")
    print(f"  Binary Cross-Entropy    : {bce:.4f}")

    print("\nConfusion Matrix:")
    print(confusion_matrix(Y_test, Y_pred))

    print("\nClassification Report:")
    print(
        classification_report(
            Y_test, Y_pred, target_names=["Worse (0)", "Better (1)"], zero_division=0
        )
    )

    print("-" * 70)
    print("TOP LEARNED FEATURE WEIGHT COEFFICIENTS")
    print("-" * 70)
    coefs = model.coef_[0]
    top_pos_idx = np.argsort(coefs)[::-1][:5]
    top_neg_idx = np.argsort(coefs)[:5]

    print("Top Positive Weights:")
    for idx in top_pos_idx:
        print(f"  Feature index {idx:2d} : {coefs[idx]:+.4f}")
    print("Top Negative Weights:")
    for idx in top_neg_idx:
        print(f"  Feature index {idx:2d} : {coefs[idx]:+.4f}")
    print("=" * 70)

    return model, feature_pipeline


if __name__ == "__main__":
    run_training_pipeline()
