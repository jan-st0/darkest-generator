from dataclasses import dataclass, field
from multiprocessing import Value
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

    def has_stun(self) -> bool:
        return self.chance_lvl1 is not None and self.chance_lvl5 is not None

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
    target: str
    can_target_self: bool
    is_percent: bool
    min_lvl1: Optional[float]
    max_lvl1: Optional[float]
    min_lvl5: Optional[float]
    max_lvl5: Optional[float]
    raw: str = ""

    def calc_max_expected_heal_effect(self) -> float:
        if self.min_lvl5 is not None and self.max_lvl5 is not None:
            return (self.min_lvl5 + self.max_lvl5) / 2
        return 0.0

    def calc_expected_heal(self, max_hp: float) -> float:
        """Calculates expected heal for a single recipient using level 5 values."""
        base_val = self.calc_max_expected_heal_effect()
        if self.is_percent:
            return (base_val / 100.0) * max_hp
        return base_val


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

    def is_target_team(self) -> bool:
        return self.target in {'self', 'ally', 'party'}

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
    heal: tuple[HealEffect, ...]
    stress_heal: StressHealEffect
    movement: MovementEffect
    buffs: tuple[BuffDebuffEffect, ...]
    debuffs: tuple[BuffDebuffEffect, ...]
    effects_raw: str
    form: Optional[str] = None
    coupled_skills: tuple[CombatSkill, ...] = field(init=False, default_factory=tuple)

    def has_healing(self) -> bool:
        """Checks if the skill provides any HP healing via direct heal effects or buff effects."""
        return bool(self.heal) or any(b.stat == 'HEAL' for b in self.buffs)
    
    def has_stun(self) -> bool:
        return self.stun.has_stun()
    
    def amount_of_targets(self) -> int:
        return 1 if not self.is_aoe else len(self.target_ranks)

    def is_self_heal(self) -> bool:
        """Checks if the skill contains a self-healing effect."""
        return any(
            h.can_target_self or h.target == 'self'
            for h in self.heal
            if h.min_lvl5 is not None
        )

    def is_buff(self) -> bool:
        return self.type == 'Buff'


    def is_debuff(self) -> bool:
        return self.target_type == 'enemy' and any(d.is_target_enemy() for d in self.debuffs)

    def buffs_formated(self) -> tuple[tuple[str, float], ...]:
        return tuple(
            (buff.stat, buff.max_val)
            for buff in self.buffs
        )

    def debuffs_formated(self) -> tuple[tuple[str, float], ...]:
        return tuple(
            (debuff.stat, debuff.max_val)
            for debuff in self.debuffs
            if debuff.is_target_enemy()
        )

    def _healing_from_buffs(self, max_hp: float) -> float:
        """Calculates expected HP healing contribution from skill buffs (e.g. Regeneration/Restoration)."""
        total = 0.0
        for buff in self.buffs:
            if buff.stat != 'HEAL' or buff.val_lvl5 is None:
                continue

            num_targets = len(self.target_ranks) if self.is_aoe and self.target_ranks else 1
            duration = buff.duration if buff.duration is not None else 1
            rate = (buff.val_lvl5 / 100.0) * max_hp if buff.value_type == 'percent' else buff.val_lvl5
            total += rate * duration * num_targets
        return total

    def healing_value(self, hero: Hero) -> float:
        """Calculates total expected HP healing output across all targets (direct heals + buff heals)."""
        max_hp = float(hero.base_stats_lvl6.HP)
        total_heal = 0.0

        for h in self.heal:
            per_target = h.calc_expected_heal(max_hp)
            match h.target:
                case 'party':
                    num_targets = len(self.target_ranks) if self.is_aoe and self.target_ranks else 4
                case 'ally':
                    num_targets = len(self.target_ranks) if self.is_aoe and self.target_ranks else 1
                case 'self' | _:
                    num_targets = 1
            total_heal += per_target * num_targets

        total_heal += self._healing_from_buffs(max_hp)
        return total_heal


    def raw_expected_damage(self, hero: Hero) -> float:
        if self.type not in {'Ranged', 'Melee'}:
            return 0.0

        dmg_mod = self.stats_lvl5.dmg_mod or 0.0
        modifier = (100.0 + dmg_mod) / 100

        skill_crit = self.stats_lvl5.crit or 0.0
        hero_crit = hero.get_max_crit()

        crit_chance = (skill_crit + hero_crit) / 100
        dmg_interval = hero.parse_base_dmg()
        dmg_exp = (dmg_interval[0] + dmg_interval[1]) / 2
        dmg_exp *= modifier
        
        crit_multiplier = 2.0
        dmg_exp = (crit_chance * crit_multiplier + (1 - crit_chance)) * dmg_exp

        targets = self.amount_of_targets()

        return dmg_exp * targets

    @property
    def forward_stat(self) -> int:
        return self.movement.forward
    
    @property
    def back_stat(self) -> int:
        return self.movement.back
    
    @property
    def move_val(self) -> int:
        """ returns signed int value for self hero movement, where negative means they move backwards """
        return self.movement.forward - self.back_stat or 0
    
    def has_backline_reach(self) -> bool:
        return self.target_type == 'enemy' and (3 in self.target_ranks or 4 in self.target_ranks)

    def stun_targets_and_chance(self) -> tuple[int, float]:
        return (self.amount_of_targets(), self.stun.chance_lvl5 or 0.0)
    
    def _dot_data(self, effect: DotEffect) -> tuple[int, int, float]:
        return (int(effect.pts_lvl5 or 0), effect.duration or 0, effect.chance_lvl5 or 0.0)
    
    def bleed_values(self) -> tuple[int, int, float]:
        return self._dot_data(self.bleed)
    
    def blight_values(self) -> tuple[int, int, float]:
        return self._dot_data(self.blight)
    
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
    def parse_base_dmg(self) -> tuple[int, ...]:
        raw_dmg = self.base_stats_lvl6.Base_DMG
        numbers = raw_dmg.split('-')
        if len(numbers) != 2:
            raise ValueError(f'Hero base damage has invalid format with {self.class_name=} {self.base_stats_lvl6.Base_DMG}')
        return tuple(map(int, numbers))
    
    def get_max_crit(self, default = 0.0) -> float:
        # TODO: extract cirt value in a more robust way
        try:
            return  float(self.base_stats_lvl6.Crit.replace('%', ''))
        except (ValueError, TypeError):
            return default

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
    active_skills: tuple[CombatSkill, ...] = field(init=False, default_factory=tuple)

    def backline_damage(self) -> float:
        total = 0.0
        for skill in self.active_skills:
            if skill.has_backline_reach():
                total += skill.raw_expected_damage(self.hero)
        return total

@dataclass(frozen=True, slots=True)
class Party:
    members: tuple[HeroBuild, ...]
