from desire_vector import DVectorManager
from game_data_manager import GameDataManager
from game_data_manager import Party
from sklearn.pipeline import Pipeline
import numpy as np

# enemy debuffs, Healing, Buffs/self-debuffs, 
# Self-healing, Raw Damage, Backline, Skill completion,
# bleed, blight, stuns, skill reach, trinket value,
# number of active skills
CATEGORIES_LEN = 13


def party_to_category_vector(party: Party, man: GameDataManager, dvec: DVectorManager):
    output = np.zeros(CATEGORIES_LEN)
    # enemy debuffs
    debf = np.zeros_like(len(dvec.debuff))
    for skill, _ in party.skill_tuple:
        debf += man.skills_debuff_values.get(skill, 0)
    output[0] = np.dot(debf, dvec.debuff)

    #Healing
    



class Ranker:
    def category_pipeline():


def score_party(team_comp: Party) -> float:
    pass