import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import SplineTransformer, StandardScaler

from game_data_manager import GameDataManager
from party_vectorizer.desire_vector import DVectorManager
from persistence import PartyDB, PartyDomainMapper

from .fitness import UNSCALED_CATEGORIES, CatVec, party_to_category_vector


def parse_data_from_db(
    db: PartyDB, mapper: PartyDomainMapper, gman: GameDataManager, dvec: DVectorManager
):
    reqs = db.load_all_records()
    # make teams_h better teams (higher) and teams_l worse (lower)
    teams_h, teams_l = [], []

    for request in reqs:
        vec_1 = party_to_category_vector(
            mapper.to_party_domain(request.party_1), gman, dvec
        )
        vec_2 = party_to_category_vector(
            mapper.to_party_domain(request.party_2), gman, dvec
        )
        if request.better == 1:
            teams_h.append(vec_1)
            teams_l.append(vec_2)
        elif request.better == 2:
            teams_h.append(vec_2)
            teams_l.append(vec_1)
    teams_h_np = np.vstack(teams_h)
    teams_l_np = np.vstack(teams_l)
    return teams_h_np, teams_l_np


def scale_teams(teams: CatVec) -> CatVec:
    scaled = teams.copy()
    scaled[:, UNSCALED_CATEGORIES] = StandardScaler().fit_transform(
        scaled[:, UNSCALED_CATEGORIES]
    )
    return scaled


def create_splines(teams: CatVec) -> CatVec:
    transformer = SplineTransformer(degree=1, n_knots=3)
    return transformer.fit_transform(teams)


def create_diff_vectors(teams_h: CatVec, teams_l: CatVec):
    if len(teams_h) != len(teams_l):
        raise ValueError("Invalid teams lenghts")

    diff_pos = teams_h - teams_l
    diff_neg = teams_l - teams_h
    X = np.vstack([diff_pos, diff_neg])
    Y = np.vstack([np.ones(len(diff_pos)), np.zeros(len(diff_neg))])
    return X, Y


def train_log_reg(X: CatVec, Y: CatVec) -> LogisticRegression:
    model = LogisticRegression(C=1.0, l1_ratio=2.0)
    model.fit(X, Y)
    return model


def team_pipeline(team_catv: CatVec) -> CatVec:
    return create_splines(scale_teams(team_catv))


def predict_team_score(model: LogisticRegression, team_catv: CatVec) -> float:
    team_vec = team_pipeline(team_catv)
    return model.coef_ @ team_vec
