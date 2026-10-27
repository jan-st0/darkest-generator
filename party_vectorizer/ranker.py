from typing import Any, cast
from pathlib import Path
from typing import Self

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize
from sklearn.base import BaseEstimator, RegressorMixin
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

from file_manager import FilePaths, load_model, save_model
from game_data_manager import GameDataManager
from game_utility import GameContext
from persistence import JsonlDB, PartyDB

from .fitness import UNSCALED_CATEGORIES, CatVec, party_to_category_vector

class Ranker(BaseEstimator, RegressorMixin):
    def __init__(self, weights: CatVec, preprocessor: Pipeline | None = None) -> None:
        self.weights = np.asarray(weights, dtype=np.float64)
        self.preprocessor = preprocessor

    def fit(self, X, y=None) -> Self:
        return self

    def predict(self, X: CatVec) -> float | np.ndarray:
        X_arr = np.asarray(X)
        features = X_arr
        if self.preprocessor is not None and X_arr.shape[-1] != len(self.weights):
            features = self.preprocessor.transform(np.atleast_2d(X_arr))

        if features.ndim == 1:
            return float(np.dot(self.weights, features))

        scores = np.dot(features, self.weights)
        if X_arr.ndim == 1 and scores.size == 1:
            return float(scores.item())
        return scores

    def save(self, path: Path | str = FilePaths.RANKER_MODEL.value) -> Path:
        return save_model(self, path)

    @classmethod
    def load(cls, path: Path | str = FilePaths.RANKER_MODEL.value) -> Self:
        return load_model(path)


def plot_training_loss(
    iterations: list[int],
    train_losses: list[float],
    test_losses: list[float] | None = None,
    save_path: Path | str | None = FilePaths.LOSS_PLOT.value,
    show: bool = False,
) -> Path | None:
    if not show:
        matplotlib.use("Agg")

    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.plot(
        iterations,
        train_losses,
        label="Training Loss (BCE)",
        color="#1f77b4",
        linewidth=2,
        marker="o" if len(iterations) <= 25 else None,
        markersize=4,
    )
    if test_losses and len(test_losses) == len(iterations):
        ax.plot(
            iterations,
            test_losses,
            label="Validation/Test Loss (BCE)",
            color="#d62728",
            linewidth=2,
            linestyle="--",
            marker="s" if len(iterations) <= 25 else None,
            markersize=4,
        )

    ax.set_title(
        "Darkest Dungeon - Party Ranker Loss Progression (BFGS)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("BFGS Iteration", fontsize=11)
    ax.set_ylabel("Binary Cross-Entropy Loss", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9)

    if len(iterations) == 1:
        ax.set_xlim(0.5, 1.5)

    fig.tight_layout()

    saved_file: Path | None = None
    if save_path:
        saved_file = Path(save_path)
        saved_file.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(saved_file, dpi=300, bbox_inches="tight")

    if show:
        plt.show()

    plt.close(fig)
    return saved_file


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


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -250, 250)))


def compute_loss_history_bfgs(
    X_train: np.ndarray,
    Y_train: np.ndarray,
    X_test: np.ndarray | None = None,
    Y_test: np.ndarray | None = None,
    C: float = 1.0,
    max_iter: int = 500,
) -> tuple[LogisticRegression, list[int], list[float], list[float]]:
    n_samples, n_features = X_train.shape
    l2_reg = 1.0 / C

    def eval_pure_bce(w: np.ndarray, X: np.ndarray, Y: np.ndarray) -> float:
        p = np.clip(_sigmoid(X @ w), 1e-15, 1.0 - 1e-15)
        return float(-np.mean(Y * np.log(p) + (1.0 - Y) * np.log(1.0 - p)))


    def loss_func(w: np.ndarray) -> float:
        p = _sigmoid(X_train @ w)
        p_clipped = np.clip(p, 1e-15, 1.0 - 1e-15)
        bce = -np.mean(Y_train * np.log(p_clipped) + (1.0 - Y_train) * np.log(1.0 - p_clipped))
        reg = 0.5 * (l2_reg / n_samples) * np.dot(w, w)
        return float(bce + reg)

    def grad_func(w: np.ndarray) -> np.ndarray:
        p = _sigmoid(X_train @ w)
        return (1.0 / n_samples) * (X_train.T @ (p - Y_train)) + (l2_reg / n_samples) * w


    w0 = np.zeros(n_features)
    iters: list[int] = [0]
    tr_losses: list[float] = [eval_pure_bce(w0, X_train, Y_train)]
    te_losses: list[float] = (
        [eval_pure_bce(w0, X_test, Y_test)] if X_test is not None and Y_test is not None else []
    )

    iteration_counter = [0]

    def callback(w_k: np.ndarray[tuple[int], np.dtype[np.float64]]) -> None:
        iteration_counter[0] += 1
        iters.append(iteration_counter[0])
        tr_losses.append(eval_pure_bce(w_k, X_train, Y_train))
        if X_test is not None and Y_test is not None:
            te_losses.append(eval_pure_bce(w_k, X_test, Y_test))

    res = minimize(
        fun=loss_func,
        x0=w0,
        method="BFGS",
        jac=grad_func,
        callback=cast(Any, callback),
        options={"maxiter": max_iter, "gtol": 1e-5},
    )

    model = LogisticRegression(C=C, fit_intercept=False)
    model.classes_ = np.unique(Y_train)
    model.coef_ = res.x.reshape(1, -1)
    model.intercept_ = np.array([0.0])
    model.n_iter_ = np.array([res.nit])

    return model, iters, tr_losses, te_losses


def predict_team_score(
    model: Ranker,
    team_catv: CatVec,
) -> float:
    return float(model.predict(team_catv))


def run_training_pipeline(
    export_model: bool = True,
    model_path: Path | str = FilePaths.RANKER_MODEL.value,
    plot_path: Path | str | None = FilePaths.LOSS_PLOT.value,
    show_plot: bool = False,
) -> Ranker:
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

    # 4. Train model using BFGS and track loss history smoothly
    model, iters, tr_losses, te_losses = compute_loss_history_bfgs(
        X_train, Y_train, X_test, Y_test, C=1.0
    )

    # 5. Create integrated Ranker scoring model
    scoring_model = Ranker(model.coef_[0], preprocessor=feature_pipeline)

    # 6. Predict & compute metrics on test set
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

    scores_h = np.array([scoring_model.predict(vec) for vec in h_test])
    scores_l = np.array([scoring_model.predict(vec) for vec in l_test])
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

    saved_plot = plot_training_loss(
        iters, tr_losses, te_losses, save_path=plot_path, show=show_plot
    )
    if saved_plot:
        print(f"Loss visualization exported to: {saved_plot}")

    if export_model:
        saved_model_path = scoring_model.save(model_path)
        print(f"Ranker model serialized and exported to: {saved_model_path}")

    return scoring_model