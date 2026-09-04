import re
from typing import Any, Union, Optional
from pathlib import Path
from dataclasses import dataclass
from file_manager import GameDataHandler
from functools import cached_property

@dataclass(frozen=True, slots=True)
class Metadata:
    game: str
    source_grounded: bool
    description: str
    hero_classes_count: int
    trinkets_count: int
    trinket_sets_count: int

@dataclass(frozen=True, slots=True)
class BaseStatsLvl0:
    HP: int
    Dodge: float
    SPD: int
    Crit: str
    Base_DMG: str
    Religious: str

@dataclass(frozen=True, slots=True)
class BaseStatsLvl6:
    HP: int
    Dodge: float
    SPD: int
    Crit: str
    Base_DMG: str

@dataclass(frozen=True, slots=True)
class CombatEffect:
    raw: str
    type: str
    detail: Optional[str] = None
    lvl_1: Optional[Union[int, float]] = None
    lvl_5: Optional[Union[int, float]] = None
    unit: Optional[str] = None

@dataclass(frozen=True, slots=True)
class CombatSkill:
    name: str
    launch_ranks: tuple[int, ...]
    target_ranks: Union[str, tuple[Union[int, str], ...]]
    type: str
    effects: tuple[CombatEffect, ...]
    effects_raw: str
    form: Optional[str] = None

    def is_self_heal(self) -> bool:
        has_heal_effect = any(
            (effect.type == 'Heal' or 'heal' in effect.raw.lower()) and not self.type == 'Stress heal'
            for effect in self.effects
        )
        if not has_heal_effect:
            return False

        VALID_SELF_TARGETS = {'Self', (4, 3, 2, 1)}
        if self.target_ranks in VALID_SELF_TARGETS:
            return True

        return any('self: heal' in eff.raw.lower() or 'self-heal' in eff.raw.lower() for eff in self.effects)

@dataclass(frozen=True, slots=True)
class CampingSkill:
    name: str
    cost: int
    effects: str

@dataclass(frozen=True, slots=True)
class Hero:
    class_name: str
    base_stats_lvl0: BaseStatsLvl0
    base_stats_lvl6: BaseStatsLvl6
    special_mechanics: str
    combat_skills: tuple[CombatSkill, ...]
    camping_skills: tuple[CampingSkill, ...]

@dataclass(frozen=True, slots=True)
class TrinketEffect:
    stat: str
    raw: str
    modifier: Optional[int] = None
    unit: Optional[str] = None
    condition: Optional[str] = None

@dataclass(frozen=True, slots=True)
class Trinket:
    name: str
    rarity: str
    category: str
    effects: tuple[TrinketEffect, ...]
    class_restriction: Optional[str] = None

@dataclass(frozen=True, slots=True)
class TrinketRef:
    name: str
    effects: tuple[TrinketEffect, ...]

@dataclass(frozen=True, slots=True)
class TrinketSet:
    set_name: str
    class_name: str
    trinket_1: TrinketRef
    trinket_2: TrinketRef
    set_bonus: tuple[TrinketEffect, ...]
    set_bonus_raw: str

def parse_combat_effect(data: dict[str, Any]) -> CombatEffect:
    return CombatEffect(**data)


def parse_combat_skill(data: dict[str, Any]) -> CombatSkill:
    target_ranks = data["target_ranks"]
    if isinstance(target_ranks, list):
        target_ranks = tuple(target_ranks)

    return CombatSkill(
        **{
            **data,
            "launch_ranks": tuple(data["launch_ranks"]),
            "target_ranks": target_ranks,
            "effects": tuple(parse_combat_effect(eff) for eff in data["effects"]),
        }
    )


def parse_camping_skill(data: dict[str, Any]) -> CampingSkill:
    return CampingSkill(**data)


def parse_hero(data: dict[str, Any]) -> Hero:
    return Hero(
        **{
            **data,
            "base_stats_lvl0": BaseStatsLvl0(**data["base_stats_lvl0"]),
            "base_stats_lvl6": BaseStatsLvl6(**data["base_stats_lvl6"]),
            "combat_skills": tuple(parse_combat_skill(s) for s in data["combat_skills"]),
            "camping_skills": tuple(parse_camping_skill(s) for s in data["camping_skills"]),
        }
    )


def parse_trinket_effect(data: dict[str, Any]) -> TrinketEffect:
    return TrinketEffect(**data)


def parse_trinket(data: dict[str, Any]) -> Trinket:
    return Trinket(
        **{
            **data,
            "effects": tuple(parse_trinket_effect(eff) for eff in data["effects"]),
        }
    )


def parse_trinket_ref(data: dict[str, Any]) -> TrinketRef:
    return TrinketRef(
        **{
            **data,
            "effects": tuple(parse_trinket_effect(eff) for eff in data["effects"]),
        }
    )


def parse_trinket_set(data: dict[str, Any]) -> TrinketSet:
    return TrinketSet(
        set_name=data["set_name"],
        class_name=data["class"],
        trinket_1=parse_trinket_ref(data["trinket_1"]),
        trinket_2=parse_trinket_ref(data["trinket_2"]),
        set_bonus=tuple(parse_trinket_effect(eff) for eff in data["set_bonus"]),
        set_bonus_raw=data["set_bonus_raw"],
    )


def parse_raw_game_data(
    raw_data: dict[str, Any],
) -> dict[str, Union[Metadata, tuple[Hero, ...], tuple[Trinket, ...], tuple[TrinketSet, ...]]]:
    return (
        Metadata(**raw_data["metadata"]),
        tuple(parse_hero(h) for h in raw_data["heroes"].values()),
        tuple(parse_trinket(t) for t in raw_data["trinkets"]),
        tuple(parse_trinket_set(s) for s in raw_data["trinket_sets"])
    )

def calculate_max_self_heal(skill: CombatSkill, hero: Hero) -> float:
    for effect in skill.effects:
        text = effect.raw.lower()
        if 'heal' not in text:
            continue
        # Matches all integers or decimals immediately followed by a '%' symbol.
        # Captures digits with an optional non-capturing decimal group (?:\.\d+).
        percentage_match = re.findall(r'(\d+(?:\.\d+)?)%', text)
        if percentage_match:
            max_pct = float(percentage_match[-1])
            hero_max_hp = float(hero.base_stats_lvl6.HP)
            return (max_pct / 100.0) * hero_max_hp
        # Matches skill level progression ranges: "A-B [hp] to C-D hp".
        # Captures 4 numbers: Group 1 & 2 (initial range), Group 3 & 4 (maxed rank range).
        # Handles hyphen/en-dash variants ([-–]), optional whitespace (\s*), and optional "hp" before "to".
        progression_match = re.search(
            r'(\d+)\s*[-–]\s*(\d+)\s+(?:hp\s+)?to\s+(\d+)\s*[-–]\s*(\d+)\s*hp',
            text
        )
        if progression_match:
            low, high = float(progression_match.group(3)), float(progression_match.group(4))
            return (low + high) / 2.0
        # Matches a standard single range: "A-B hp" or "A to B hp".
        # Captures minimum (Group 1) and maximum (Group 2) values separated by a hyphen, en-dash, or "to".
        range_match = re.search(r'(\d+)\s*(?:[-–]|to)\s*(\d+)\s*hp', text)
        if range_match:
            return (float(range_match.group(1)) + float(range_match.group(2))) / 2.0
        # Matches a static, flat heal amount: "X hp".
        # Captures the integer value directly preceding the literal "hp".
        single_match = re.search(r'(\d+)\s*hp', text)
        if single_match:
            return float(single_match.group(1))

    return 0.0


class GameDataManager:

    def __init__(self, file_path: Optional[Union[Path, str]] = None) -> None:
        if file_path is None:
            self._handler = GameDataHandler()
        else:
            self._handler = GameDataHandler(file_path)
        parsed_data = parse_raw_game_data(self._handler.raw_data)
        self._metadata, self._heroes, self._trinkets, self._trinket_sets = parsed_data
    
    @cached_property
    def self_heal_skills(self) -> tuple[tuple[CombatSkill, Hero], ...]:
        """Sorted by healing effect"""
        unsorted_skills = tuple(
            (skill, hero)
            for hero in self._heroes
            for skill in hero.combat_skills
            if skill.is_self_heal()
        )
        return sorted(unsorted_skills, key=lambda pair: calculate_max_self_heal(pair[0], pair[1]), reverse=True)
        

man = GameDataManager()
unique = [(hero.class_name, skill.name) for skill, hero in man.self_heal_skills]
print(unique)