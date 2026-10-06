from party_vectorizer.desire_vector import DVectorManager
from game_data_manager import GameDataManager
import numpy as np

from data_model.party_data_model import Party

# enemy debuffs, Healing, Buffs/self-debuffs, 
# Self-healing, Raw Damage, Backline, vs stunned present, 
# vs stunned synergy while present, vs marked present,
# vs marked synergy while present
# bleed, blight, stuns, 
# skill reach pos 1, skill reach pos 2, 
# skill reach pos 3, skill reach pos 4, trinket value,
# number of active skills
CATEGORIES_LEN = 19


def party_to_category_vector(party: Party, man: GameDataManager, dvec: DVectorManager):
    output = np.zeros(CATEGORIES_LEN, dtype=np.float64)
    # enemy debuffs (unscaled)
    debf = np.zeros(len(dvec.debuff), dtype=np.float64)
    for skill, _ in party.skill_parent_tuple:
        debf += man.skills_debuff_values.get(skill, 0)
    output[0] = np.dot(debf, dvec.debuff)

    #Healing
    output[1] = (
        party.members[0].max_heal 
        + party.members[1].max_heal
        + party.members[2].max_heal 
        + party.members[3].max_heal
    )

    output[1] /= man.max_skill_heal * 4
    # Buffs (unscaled)
    for skill, supplier in party.skill_parent_tuple:
        if skill not in man.skills_buff_values.keys():
            continue
        buff_v = man.skills_buff_values[skill]
        target_t = skill.target_type
        out = 0.0
        match target_t:
            case 'ally':
                out = max(np.dot(buff_v, dvec.vec.get(hero.name, 0)) for hero in party.members if hero is not supplier)
            
            case 'party':
                out = sum(np.dot(buff_v, dvec.vec.get(hero.name, 0)) for hero in party.members if hero is not supplier)
            
            case 'self':
                out = np.dot(buff_v, dvec.vec.get(supplier.name, 0))
        output[2] += out
    
    # Self-heal
    output[3] = (
        party.members[0].max_self_heal_skill 
        + party.members[1].max_self_heal_skill
        + party.members[2].max_self_heal_skill
        + party.members[3].max_self_heal_skill
    )
    output[3] /= man.max_skill_self_heal * 4
    # Raw damage
    output[4] = (
        party.members[0].max_raw_dmg 
        + party.members[1].max_raw_dmg
        + party.members[2].max_raw_dmg
        + party.members[3].max_raw_dmg
    )

    output[4] /= man.max_skill_dps * 4
    
    # Backline
    output[5] = (
        party.members[0].backiline_dmg 
        + party.members[1].backiline_dmg
        + party.members[2].backiline_dmg
        + party.members[3].backiline_dmg
    )

    output[5] /= man.max_skill_backline_dmg * 4
    # Skill completions -- for now the once with 'vs stunned' or 'vs marked' conditions

    # stunned - 5, 6 indices
    vs_stunned_present = not man.vs_stunned_skills.isdisjoint(party.all_active_skills)
    output[6] = 1.0 if vs_stunned_present else 0.0
    output[7] = 1.0 if vs_stunned_present and party.has_stun else 0.0

    # marked - 7, 8 indices
    vs_marked_present = not man.vs_marked_skills.isdisjoint(party.all_active_skills)
    output[8] = 1.0 if vs_marked_present else 0.0
    output[9] = 1.0 if vs_marked_present and party.has_mark else 0.0

    # bleed
    output[10] = (
        party.members[0].max_bleed
        + party.members[1].max_bleed
        + party.members[2].max_bleed
        + party.members[3].max_bleed
    )

    output[10] /= man.max_skill_bleed * 4

    #blight
    output[11] = (
        party.members[0].max_blight
        + party.members[1].max_blight
        + party.members[2].max_blight
        + party.members[3].max_blight
    )

    output[11] /= man.max_skill_blight * 4

    # stuns 
    output[12] = (
        party.members[0].stuns_num
        + party.members[1].stuns_num
        + party.members[2].stuns_num
        + party.members[3].stuns_num
    )

    output[12] /= man.max_skill_stun * 4

    # Skill reach
    reach = [0] * 4
    MAX_POSSIBLE_REACH = 16 # all skills can hit certain position
    for skill, supplier in party.skill_parent_tuple:
        if skill.target_type != 'enemy':
            continue
        for pos in skill.target_ranks:
            reach[pos-1] += 1

    output[13] = reach[0] / MAX_POSSIBLE_REACH
    output[14] = reach[1] / MAX_POSSIBLE_REACH
    output[15] = reach[2] / MAX_POSSIBLE_REACH
    output[16] = reach[3] / MAX_POSSIBLE_REACH

    # trinket value (unscaled)
    output[17] = dvec.process_trinket_scores(party, man)
    output[18] = len(party.skill_parent_tuple) / 16

    return output




class Ranker:
    def category_pipeline():
        pass

def score_party(team_comp: Party) -> None:
    pass