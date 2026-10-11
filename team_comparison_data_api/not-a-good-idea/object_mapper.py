from pydantic import Field
from typing import Annotated
from pydantic import BaseModel
from typing import Iterable

from data_model.party_data_model import Party
from data_model.hero_data_model import CombatSkill, Hero, HeroBuild
from enum import StrEnum

from data_model.trinket_data_model import Trinket
from game_data_manager import GameDataManager






# TODO: implement a better design in future versions
COL_NUM = 2 * ( 4 * (4 + 2)) + 1

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

def all_columns() -> list[str]:
    """Returns names of all columns"""
    out = []
    for p_idx in range(1, 3):
        for h_idx in range(1, 5):
            out.append(str_hero_col(h_idx, p_idx))
            out += [str_skill_col(h_idx, s_idx, p_idx) for s_idx in range(1, 5)]
            out += [str_trinket_col(h_idx, t_idx, p_idx) for t_idx in range(1, 3)]
    return out

def party_pair_to_csv_row(party1: Party, party2: Party, better: int) -> dict[str, str | int]:
    """Csv row is a dict for pandas that represents a row"""
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
            str_skill_col(4 - h_idx, s_idx, idx): skill.name
            for h_idx, hero in enumerate(party.members)
            for s_idx, skill in enumerate(hero.skills)           
        }
    
    out |= {TableCols.BETTER: better}
    return out

def csv_to_party_tuple(row: dict[str, str], gman: GameDataManager) -> tuple[Party, Party, int]:
    # Allow for null/-1 better - not scored
    better = int(row.get(TableCols.BETTER, -1))
    return (
        csv_to_party(row, 1, gman),
        csv_to_party(row, 2, gman),
        better
    )

def csv_to_party(row: dict[str, str], party_idx: int, gman: GameDataManager) -> Party:
    return Party(
        tuple(csv_to_hero_build(row, party_idx, h_idx, gman) for h_idx in range(1, 5, -1)), gman
    )

def _filter_none_tuple(iterable: Iterable) -> tuple:
    return tuple(item for item in iterable if item is not None)

def csv_to_hero_build(row: dict[str, str], party_idx: int, hero_idx: int, gman: GameDataManager) -> HeroBuild:
    # TODO: log if not found
    hero = gman.heroes_by_name.get(
        row.get(str_hero_col(hero_idx, party_idx), ''), None
    )
    if hero is None:
        raise KeyError(f'Hero object is None for this name: {str_hero_col(hero_idx, party_idx)}')


    skills: tuple[CombatSkill, ...] = _filter_none_tuple(
        csv_to_skill(row, party_idx, hero_idx, skill_idx, gman)
        for skill_idx in range(1, 5)
    )

    if len(skills) != 4:
        s_tuple = ', '.join(
            s.name
            for s in skills
        )
        raise KeyError(f'Skills tuple is incorrect:\n {s_tuple} \n length: {len(skills)}')

    trinkets = _filter_none_tuple(
        csv_to_trinket(row, party_idx, hero_idx, trinket_idx, gman)
        for trinket_idx in range(1, 3)
    )

    return HeroBuild(
        hero,
        hero_idx,
        skills,
        trinkets
    )

def csv_to_trinket(row: dict[str, str], party_idx: int, hero_idx, trinket_idx: int, gman: GameDataManager) -> Trinket| None:
    # TODO: log if not found
    return gman.trinkets_by_name.get(
        row.get(str_trinket_col(hero_idx, trinket_idx, party_idx), ''), None
    )

def csv_to_skill(row: dict[str, str], party_idx: int, hero_idx: int, skill_idx: int, gman: GameDataManager) -> CombatSkill| None:
    # TODO: log if not found
    return gman.skills_by_name.get(
        row.get(str_skill_col(hero_idx, skill_idx, party_idx), ''), None
    )

