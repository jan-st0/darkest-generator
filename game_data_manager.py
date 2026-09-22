import numpy as np
from typing import Union, Optional
from pathlib import Path
from file_manager import GameDataHandler, FilePaths
from functools import cached_property
from itertools import chain, product
from collections.abc import Iterator
from hero_data_model import (
    CombatSkill,
    Hero,
    Metadata,
)
from trinket_data_model import (
    Trinket,
    TrinketEvaluationContext,
    TrinketSet
)
from trinket_evaluator import (
    ALL_IGNORED_TRINKETS,
    UTILITY_STATS,
    evaluate_trinket_stats,
    is_trinket_ignored,
)
from yaml_parser import parse_raw_game_data

# Shows how buffs/debuffs should be sorted
# Eg: for a buff if dmg1 > dmg2 then dmg1 is better, but for debuff the other way
STAT_DESIRABILITY: dict[str, int] = {
    "DMG": +1,
    "SPD": +1,
    "ACC": +1,
    "CRIT": +1,
    "PROT": +1,
    "DODGE": +1,
    "BLIGHT_RESIST": +1,
    "BLEED_RESIST": +1,
    "HEAL_RECEIVED": +1,
    "STRESS": -1,
    "STRESS_RECEIVED": -1,
    "DMG_TAKEN": -1,
    "HEALING_SKILLS": +1,
    "TORCH": +1,
    "BLIGHT_CHANCE": +1,
    "DEBUFF_RESIST": +1,
    "MOVE_RESIST": +1,
}

def calculate_max_self_heal(skill: CombatSkill, hero: Hero) -> float:
    max_hp = float(hero.base_stats_lvl6.HP)
    self_heals = [
        h.calc_expected_heal(max_hp)
        for h in skill.heal
        if h.can_target_self or h.target == 'self'
    ]
    # Also check if any buff provides self-healing
    buff_self_heals = [
        ((b.val_lvl5 / 100.0) * max_hp if b.value_type == 'percent' else b.val_lvl5) * (b.duration or 1)
        for b in skill.buffs
        if b.stat == 'HEAL' and b.target == 'self' and b.val_lvl5 is not None
    ]
    all_self_heals = self_heals + buff_self_heals
    return max(all_self_heals, default=0.0)


def calculate_max_dps(skill: CombatSkill, hero: Hero) -> float:
    return skill.raw_expected_damage(hero)


class GameDataManager:

    # torch is not hero specific buff, like stress heal
    EXCLUDED_BUFF_TYPES = {'OTHER', 'STRESS_HEAL', 'CURE_BLIGHT_BLEED', 'TORCH', 'HEAL', 'RIPOSTE', 'RIPOSTE_CRIT', 'RIPOSTE_DMG'}

    EXCLUDED_DEBUFF_TYPES = {'OTHER', 'TORCH', 'RIPOSTE_DMG'}

    def __init__(self, file_path: Optional[Union[Path, str]] = None) -> None:
        target_path: Path = (
            FilePaths.GAME_INFO_SOURCE.value
            if file_path is None
            else Path(file_path)
        )
        self._handler = GameDataHandler(target_path)
        parsed_data = parse_raw_game_data(self._handler.raw_data)
        self._metadata, self._heroes, self._trinkets, self._trinket_sets = parsed_data
        self._init_skill_complements()

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

    def all_combat_skills(self) -> Iterator[CombatSkill]:
        """Returns an Iterator for all skills"""
        return chain.from_iterable(hero.combat_skills for hero in self._heroes)

    def all_combat_skill_pairs(self) -> Iterator[tuple[Hero, CombatSkill]]:
        """Returns an Iterator for all skills with pairs of hero and their skill"""
        return chain.from_iterable(
                product((hero,), hero.combat_skills) for hero in self._heroes
            )

    @cached_property
    def heroes_by_name(self) -> dict[str, Hero]:
        return {h.class_name: h for h in self._heroes}

    def calculate_max_self_heal(self, skill: CombatSkill, hero: Hero) -> float:
        return calculate_max_self_heal(skill, hero)

    def calculate_max_dps(self, skill: CombatSkill, hero: Hero) -> float:
        return calculate_max_dps(skill, hero)

    @cached_property
    def max_skill_dps(self) -> float:
        """Maximum single-skill raw expected damage across all heroes."""
        return max(
            (self.calculate_max_dps(skill, hero) for hero, skill in self.all_combat_skill_pairs()),
            default=0.0,
        )

    @cached_property
    def max_skill_self_heal(self) -> float:
        """Maximum single-skill self healing output across all heroes."""
        return max(
            (self.calculate_max_self_heal(skill, hero) for hero, skill in self.all_combat_skill_pairs()),
            default=0.0,
        )

    @cached_property
    def self_heal_skills(self) -> tuple[tuple[CombatSkill, Hero], ...]:
        """Sorted by maximum self-healing output at lvl 5"""
        unsorted_skills = tuple(
            (skill, hero)
            for hero, skill in self.all_combat_skill_pairs()
            if skill.is_self_heal()
        )




        return tuple(sorted(unsorted_skills, key=lambda pair: calculate_max_self_heal(pair[0], pair[1]), reverse=True))

    def _init_skill_complements(self) -> None:
        """Populates coupled_skills on all skills that apply mark or stun with their respective complement skills."""
        vs_marked = self.vs_marked_skills
        vs_stunned = self.vs_stunned_skills

        for skill in self.all_combat_skills():
            complements: list[CombatSkill] = []
            if skill.applies_mark():
                complements.extend(vs_marked)
            if skill.applies_stun():
                complements.extend(vs_stunned)

            if complements:
                # Deduplicate while preserving order
                seen: set[int] = set()
                deduped: list[CombatSkill] = []
                for comp in complements:
                    if id(comp) not in seen:
                        seen.add(id(comp))
                        deduped.append(comp)
                skill.coupled_skills = tuple(deduped)
            else:
                skill.coupled_skills = ()
    @cached_property
    def vs_marked_skills(self) -> tuple[CombatSkill, ...]:
        """Returns all combat skills with bonus damage or crit against marked enemies."""
        return tuple(s for s in self.all_combat_skills() if s.has_vs_marked_bonus())

    @cached_property
    def vs_stunned_skills(self) -> tuple[CombatSkill, ...]:
        """Returns all combat skills with bonus damage against stunned enemies."""
        return tuple(s for s in self.all_combat_skills() if s.has_vs_stunned_bonus())

    def get_mark_or_stun_skills(self) -> tuple[CombatSkill, ...]:
        """
        Returns only combat skills that apply mark or stun to enemies.
        Each returned skill has its `coupled_skills` populated with its complement skills
        (skills with vs marked and vs stunned bonuses).
        """
        self._init_skill_complements()
        return tuple(
            skill for skill in self.all_combat_skills()
            if skill.applies_mark_or_stun()
        )

    @cached_property
    def mark_or_stun_skills(self) -> tuple[CombatSkill, ...]:
        """Cached property giving only skills that apply mark or stun with coupled complements."""
        return self.get_mark_or_stun_skills()


    @cached_property
    def all_buff_types(self) -> tuple[str, ...]:
        types = {
            buff.stat
            for skill in self.all_combat_skills()
            if skill.is_buff()
            for buff in skill.buffs
            if buff.stat not in self.EXCLUDED_BUFF_TYPES and buff.val_lvl5 is not None
        }
        return tuple(sorted(types))

    @cached_property
    def all_debuff_types(self) -> tuple[str, ...]:
        types = {
            debuff.stat
            for skill in self.all_combat_skills()
            if skill.is_debuff()
            for debuff in skill.debuffs
            if debuff.is_target_enemy()
        }
        types -= self.EXCLUDED_DEBUFF_TYPES
        return tuple(sorted(types))

    @cached_property
    def max_values_for_buffs(self) -> dict[str, float]:
        max_vals: dict[str, float] = {}
        for skill in self.all_combat_skills():
            if not skill.is_buff():
                continue
            for stat, val in skill.buffs_formated():
                if stat in self.EXCLUDED_BUFF_TYPES:
                    continue
                if (
                    stat in max_vals
                    and val * STAT_DESIRABILITY.get(stat, 1) > max_vals[stat] * STAT_DESIRABILITY.get(stat, 1)
                ) or stat not in max_vals:
                    max_vals[stat] = val
        return max_vals

    @cached_property
    def max_values_for_debuffs(self) -> dict[str, float]:
        max_vals: dict[str, float] = {}
        for skill in self.all_combat_skills():
            for stat, val in skill.debuffs_formated():
                if stat in self.EXCLUDED_DEBUFF_TYPES:
                    continue
                if (
                    stat in max_vals
                    and -val * STAT_DESIRABILITY[stat] > STAT_DESIRABILITY[stat] * -max_vals[stat]
                ) or stat not in max_vals:
                    max_vals[stat] = val
        return max_vals

    def _vectorize_effects(
        self,
        is_applicable: str,
        effects_attr: str,
        stat_types: tuple[str, ...],
        max_map: dict[str, float],
    ) -> dict[CombatSkill, np.ndarray]:
        if not stat_types:
            return {}

        inv_max = np.array(
            [1.0 / max_map[stat] if max_map.get(stat, 0.0) != 0 else 0.0 for stat in stat_types],
            dtype=np.float64,
        )
        stat_indices = {stat: i for i, stat in enumerate(stat_types)}
        num_stats = len(stat_types)

        result: dict[CombatSkill, np.ndarray] = {}
        for skill in self.all_combat_skills():
            if not getattr(skill, is_applicable)():
                continue

            vec = np.zeros(num_stats, dtype=np.float64)
            for eff in getattr(skill, effects_attr):
                if eff.stat in stat_indices and eff.val_lvl5 is not None:
                    vec[stat_indices[eff.stat]] = eff.max_val

            result[skill] = vec * inv_max

        return result

    @cached_property
    def skills_buff_values(self) -> dict[CombatSkill, np.ndarray]:
        stat_types = self.all_buff_types
        if not stat_types:
            return {}

        max_map = self.max_values_for_buffs
        inv_max = np.array(
            [1.0 / max_map[stat] if max_map.get(stat, 0.0) != 0 else 0.0 for stat in stat_types],
            dtype=np.float64,
        )
        stat_indices = {stat: i for i, stat in enumerate(stat_types)}
        num_stats = len(stat_types)

        result: dict[CombatSkill, np.ndarray] = {}
        for skill in self.all_combat_skills():
            if not skill.is_buff():
                continue

            vec = np.zeros(num_stats, dtype=np.float64)
            for b in skill.buffs:
                if b.stat in stat_indices and b.val_lvl5 is not None:
                    vec[stat_indices[b.stat]] += b.max_val

            # Negative values for self/friendly debuffs (e.g. Revenge -10 DODGE)
            for d in skill.debuffs:
                if d.is_target_team() and d.stat in stat_indices and d.val_lvl5 is not None:
                    vec[stat_indices[d.stat]] += d.max_val

            result[skill] = vec * inv_max

        return result

    @cached_property
    def skills_debuff_values(self) -> dict[CombatSkill, np.ndarray]:
        return self._vectorize_effects(
            is_applicable="is_debuff",
            effects_attr="debuffs",
            stat_types=self.all_debuff_types,
            max_map=self.max_values_for_debuffs,
        )

    @cached_property
    def trinkets_by_name(self) -> dict[str, Trinket]:
        return {t.name: t for t in self._trinkets}

    @cached_property
    def usable_trinkets(self) -> tuple[Trinket, ...]:
        """Returns only trinkets that are not excluded per diagram.md."""
        return tuple(t for t in self._trinkets if not is_trinket_ignored(t.name))

    @cached_property
    def max_values_for_utility_stats(self) -> dict[str, float]:
        """Maximum observed absolute values for utility stats (scouting, trap disarm, surprise)."""
        max_vals: dict[str, float] = {}
        for t in self.usable_trinkets:
            stats = evaluate_trinket_stats(t)
            for k, v in stats.items():
                if k in UTILITY_STATS:
                    max_vals[k] = max(max_vals.get(k, 0.0), abs(v))
        return max_vals

    def evaluate_trinket(
        self,
        trinket: Trinket,
        context: Optional[TrinketEvaluationContext] = None,
    ) -> dict[str, float]:
        """Evaluates effective stat modifiers for a given trinket and hero context."""
        return evaluate_trinket_stats(trinket, context)


def get_mark_or_stun_skills(data_manager: Optional[GameDataManager] = None) -> tuple[CombatSkill, ...]:
    """
    Returns only combat skills that apply mark or stun to enemies,
    with their coupled complement skills populated.
    """
    if data_manager is None:
        data_manager = GameDataManager()
    return data_manager.get_mark_or_stun_skills()

