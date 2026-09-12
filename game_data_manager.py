import numpy as np
from typing import Any, Union, Optional
from pathlib import Path
from dataclasses import dataclass
from file_manager import GameDataHandler, FilePaths
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
class SkillCombatStats:
    acc: Optional[float]
    dmg_mod: Optional[float]
    crit: Optional[float]

@dataclass(frozen=True, slots=True)
class StunEffect:
    chance_lvl1: Optional[float]
    chance_lvl5: Optional[float]

@dataclass(frozen=True, slots=True)
class DotEffect:
    pts_lvl1: Optional[float]
    pts_lvl5: Optional[float]
    duration: Optional[int]
    chance_lvl5: Optional[float]

@dataclass(frozen=True, slots=True)
class MarkEffect:
    applies: bool
    target: Optional[str]
    duration: Optional[int]
    bonus_dmg_vs_marked: Optional[float]
    bonus_crit_vs_marked: Optional[float]

@dataclass(frozen=True, slots=True)
class HealEffect:
    has_heal: bool
    target: Optional[str]
    is_percent: bool
    min_lvl1: Optional[float]
    max_lvl1: Optional[float]
    min_lvl5: Optional[float]
    max_lvl5: Optional[float]

    def calc_max_expected_heal_effect(self) -> float:
        if self.min_lvl5 is not None and self.max_lvl5 is not None:
            return (self.min_lvl5 + self.max_lvl5) / 2

        return 0.0

@dataclass(frozen=True, slots=True)
class StressHealEffect:
    has_stress_heal: bool
    target: Optional[str]
    min_lvl5: Optional[float]
    max_lvl5: Optional[float]

@dataclass(frozen=True, slots=True)
class MovementEffect:
    forward: int
    back: int
    knockback: int
    pull: int

@dataclass(frozen=True, slots=True)
class BuffDebuffEffect:
    stat: str
    target: str
    value_type: str
    val_lvl1: Optional[float]
    val_lvl5: Optional[float]
    duration: Optional[int]
    chance_lvl5: Optional[float]
    raw: str

@dataclass(frozen=True, slots=True)
class CombatSkill:
    name: str
    launch_ranks: tuple[int, ...]
    target_ranks: tuple[int, ...]
    target_type: str
    is_aoe: bool
    type: str
    is_pure_buff: bool
    stats_lvl1: SkillCombatStats
    stats_lvl5: SkillCombatStats
    stun: StunEffect
    blight: DotEffect
    bleed: DotEffect
    mark: MarkEffect
    heal: HealEffect
    stress_heal: StressHealEffect
    movement: MovementEffect
    buffs: tuple[BuffDebuffEffect, ...]
    debuffs: tuple[BuffDebuffEffect, ...]
    effects_raw: str
    form: Optional[str] = None

    def _is_heal_target_ranks_4321(self) -> bool:
        return self.heal.target == 'ally' and self.target_ranks == (1, 2, 3, 4)

    def _is_not_stress_heal(self) -> bool:
        # TODO: better function name and more robust handling
        return self.heal.max_lvl5 is not None

    def is_self_heal(self) -> bool:
        return self.heal.has_heal and (self.heal.target in ('self', 'ally_and_self') or self._is_heal_target_ranks_4321()) and self._is_not_stress_heal()

    def is_buff(self) -> bool:
        return self.type == 'Buff'

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

@dataclass(frozen=True, slots=True)
class HeroBuild:
    hero: Hero
    rank: int
    skills: tuple[CombatSkill, ...]
    trinkets: tuple[Trinket, ...]

@dataclass(frozen=True, slots=True)
class Party:
    members: tuple[HeroBuild, ...]

def parse_buff_debuff(data: dict[str, Any]) -> BuffDebuffEffect:
    return BuffDebuffEffect(**data)

def parse_combat_skill(data: dict[str, Any]) -> CombatSkill:
    return CombatSkill(
        name=data["name"],
        launch_ranks=tuple(data["launch_ranks"]),
        target_ranks=tuple(data["target_ranks"]),
        target_type=data["target_type"],
        is_aoe=data["is_aoe"],
        type=data["type"],
        is_pure_buff=data["is_pure_buff"],
        stats_lvl1=SkillCombatStats(**data["stats_lvl1"]),
        stats_lvl5=SkillCombatStats(**data["stats_lvl5"]),
        stun=StunEffect(**data["stun"]),
        blight=DotEffect(**data["blight"]),
        bleed=DotEffect(**data["bleed"]),
        mark=MarkEffect(**data["mark"]),
        heal=HealEffect(**data["heal"]),
        stress_heal=StressHealEffect(**data["stress_heal"]),
        movement=MovementEffect(**data["movement"]),
        buffs=tuple(parse_buff_debuff(b) for b in data.get("buffs", [])),
        debuffs=tuple(parse_buff_debuff(d) for d in data.get("debuffs", [])),
        effects_raw=data.get("effects_raw", ""),
        form=data.get("form"),
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
    heal = skill.heal
    if not heal.has_heal:
        return 0.0

    max_hp = float(hero.base_stats_lvl6.HP)
    val = heal.calc_max_expected_heal_effect()
    if heal.is_percent:
        val = heal.max_lvl5 or heal.max_lvl1 or 0.0
        return (val / 100.0) * max_hp
    return float(val)


class GameDataManager:

    EXCLUDED_BUFF_TYPES = {'OTHER', 'STRESS_HEAL', 'CURE_BLIGHT_BLEED'}

    def __init__(self, file_path: Optional[Union[Path, str]] = None) -> None:
        if file_path is None:
            self._handler = GameDataHandler(FilePaths.GAME_INFO_SOURCE_V3.value)
        else:
            self._handler = GameDataHandler(file_path)
        parsed_data = parse_raw_game_data(self._handler.raw_data)
        self._metadata, self._heroes, self._trinkets, self._trinket_sets = parsed_data

    @property
    def metadata(self) -> Metadata:
        return self._metadata

    @property
    def heroes(self) -> tuple[Hero, ...]:
        return self._heroes

    @property
    def trinkets(self) -> tuple[Trinket, ...]:
        return self._trinkets

    @property
    def trinket_sets(self) -> tuple[TrinketSet, ...]:
        return self._trinket_sets

    @cached_property
    def heroes_by_name(self) -> dict[str, Hero]:
        return {h.class_name: h for h in self._heroes}

    @cached_property
    def self_heal_skills(self) -> tuple[tuple[CombatSkill, Hero], ...]:
        """Sorted by maximum self-healing output at lvl 5"""
        unsorted_skills = tuple(
            (skill, hero)
            for hero in self._heroes
            for skill in hero.combat_skills
            if skill.is_self_heal()
        )
        return tuple(sorted(unsorted_skills, key=lambda pair: calculate_max_self_heal(pair[0], pair[1]), reverse=True))

    @cached_property
    def all_buff_types(self) -> tuple[str, ...]:
        types = {
            buff.stat
            for hero in self._heroes
            for skill in hero.combat_skills
            if skill.is_buff()
            for buff in skill.buffs
            if buff.stat not in self.EXCLUDED_BUFF_TYPES and buff.val_lvl5 is not None
        }
        return tuple(sorted(types))

    @cached_property
    def max_values_for_buffs(self) -> dict[str, float]:
        max_vals: dict[str, float] = {}
        for hero in self._heroes:
            for skill in hero.combat_skills:
                if not skill.is_buff():
                    continue
                for buff in skill.buffs:
                    stat = buff.stat
                    if stat in self.EXCLUDED_BUFF_TYPES or buff.val_lvl5 is None:
                        continue
                    val = abs(buff.val_lvl5) if stat == 'STRESS_RECEIVED' else float(buff.val_lvl5)
                    if val > max_vals.get(stat, 0.0):
                        max_vals[stat] = val
        return max_vals

    @cached_property
    def skills_buff_values(self) -> dict[CombatSkill, np.ndarray]:
        buff_types = self.all_buff_types
        if not buff_types:
            return {}

        max_map = self.max_values_for_buffs
        # Pre-compute normalizers to replace N divisions with N multiplications: x * inv
        inv_max = np.array(
            [1.0 / max_map[stat] if max_map.get(stat, 0.0) != 0 else 0.0 for stat in buff_types],
            dtype=np.float64,
        )
        stat_indices = {stat: i for i, stat in enumerate(buff_types)}
        num_stats = len(buff_types)

        result: dict[CombatSkill, np.ndarray] = {}
        for hero in self._heroes:
            for skill in hero.combat_skills:
                if not skill.is_buff():
                    continue

                vec = np.zeros(num_stats, dtype=np.float64)
                for buff in skill.buffs:
                    if buff.stat in stat_indices and buff.val_lvl5 is not None:
                        vec[stat_indices[buff.stat]] = abs(buff.val_lvl5)

                # Vectorized scaling
                result[skill] = vec * inv_max

        return result


if __name__ == "__main__":
    man = GameDataManager()
    print('Buff order in vector:')
    for buff_type in man.all_buff_types:
        print(buff_type, end=' ')
    print('\n')
    for skill, vector in man.skills_buff_values.items():
        print(f'{skill.name=}  {vector}')
    print('\nSelf-heal skills (ordered by output):')
    for skill, hero in man.self_heal_skills:
        print(f'{hero.class_name} -> {skill.name}: {calculate_max_self_heal(skill, hero)} HP')
