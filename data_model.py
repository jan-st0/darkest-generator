from dataclasses import dataclass
from typing import Optional


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
    can_target_self: bool = False

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

    @property
    def max_val(self) -> float:
        if self.val_lvl5 is not None:
            return self.val_lvl5
        return 0.0

    def is_target_enemy(self) -> bool:
        return self.target == 'target'

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

    def is_self_heal(self) -> bool:
        return self.heal.has_heal and self.heal.can_target_self and self.heal.max_lvl5 is not None

    def is_buff(self) -> bool:
        return self.type == 'Buff'


    def is_debuff(self) -> bool:
        return self.target_type == 'enemy' and len(self.debuffs) > 0

    @property
    def buffs_formated(self) -> tuple[tuple[str, float], ...]:
        return tuple(
            (buff.stat, buff.max_val)
            for buff in self.buffs
        )

    @property
    def debuffs_formated(self) -> tuple[tuple[str, float], ...]:
        return tuple(
            (debuff.stat, debuff.max_val)
            for debuff in self.debuffs
        )

    def healing_value(self, hero: Hero) -> float:
        pass


    def raw_expected_damage(self, hero: Hero) -> float:
        if self.type not in {'Ranged', 'Melee'}:
            return 0.0

        modifier = (100 + self.stats_lvl5.dmg_mod) / 100

        crit_chance = (self.stats_lvl5.crit + hero.base_stats_lvl6.Crit) / 100
        dmg_interval = hero.parse_base_dmg()
        dmg_exp = (dmg_interval[0] + dmg_interval[1]) / 2
        dmg_exp *= modifier
        dmg_exp = crit_chance * 2 * dmg_exp + (1 - crit_chance) * dmg_exp

        targets = 1
        if self.is_aoe:
            targets = len(self.target_ranks)

        return dmg_exp * targets



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
    def parse_base_dmg(self) -> tuple[int, int]:
        numbers = self.base_stats_lvl6.Base_DMG.split('-')
        if len(numbers) != 2:
            raise ValueError(f'Hero base damage has invalid format with {self.class_name=} {self.base_stats_lvl6.Base_DMG}')
        return tuple(map(int, numbers))

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
