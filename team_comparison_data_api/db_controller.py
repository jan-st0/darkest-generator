import enum
from data_model.party_data_model import Party
from data_model.hero_data_model import HeroBuild
from enum import StrEnum

class TableCols(StrEnum):
    # hero_XZ, where X is hero position: 4, 3, 2, 1 and Z is team id(1 or 2)
    HERO_PREFIX = 'hero_'
    # trinket_XYZ, where X is hero number and Y is triket number starting from 1
    TRINKET_PREFIX = 'trinket_'
    # skill_XYZ
    SKILL_PREFIX = 'skill_'
    BETTER = 'better'


def str_hero_col(num: int, team_id: int) -> str:
    return f'{TableCols.HERO_PREFIX}{num}{team_id}'

def str_trinket_col(hero_pos: int, idx: int, team_id: int) -> str:
    return f'{TableCols.TRINKET_PREFIX}{hero_pos}{idx}{team_id}'

def str_skill_col(hero_pos: int, idx: int, team_id: int) -> str:
    return f'{TableCols.SKILL_PREFIX}{hero_pos}{idx}{team_id}'

def party_to_csv_row(party1: Party, party2: Party):
    out = {}
    for idx, party in enumerate([party1, party2]):
        # start from 1
        idx += 1
        out |= {str_hero_col(4 - i, idx): hero.name for i, hero in enumerate(party.members)}
        
        out |= {
            str_trinket_col(4 - h_idx, t_idx + 1, idx): trinket.name
            for h_idx, hero in enumerate(party.members)
            for t_idx, trinket in enumerate(hero.trinkets)
        }

        out |= {
            
        }


    