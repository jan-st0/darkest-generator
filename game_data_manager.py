import numpy as np
from typing import Union, Optional
from pathlib import Path
from file_manager import GameDataHandler, FilePaths
from functools import cached_property
from itertools import chain, product
from collections.abc import Iterator
from data_model import (
    CombatSkill,
    Hero,
    Metadata,
    Trinket,
    TrinketSet,
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


class GameDataManager:

    # torch is not hero specific buff, like stress heal
    EXCLUDED_BUFF_TYPES = {'OTHER', 'STRESS_HEAL', 'CURE_BLIGHT_BLEED', 'TORCH', 'HEAL'}

    EXCLUDED_DEBUFF_TYPES = {'OTHER', 'TORCH'}

    def __init__(self, file_path: Optional[Union[Path, str]] = None) -> None:
        if file_path is None:
            self._handler = GameDataHandler(FilePaths.GAME_INFO_SOURCE.value)
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

    @cached_property
    def self_heal_skills(self) -> tuple[tuple[CombatSkill, Hero], ...]:
        """Sorted by maximum self-healing output at lvl 5"""
        unsorted_skills = tuple(
            (skill, hero)
            for hero, skill in self.all_combat_skill_pairs()
            if skill.is_self_heal()
        )




        return tuple(sorted(unsorted_skills, key=lambda pair: calculate_max_self_heal(pair[0], pair[1]), reverse=True))

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
            for stat, val in skill.buffs_formated:
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
            for stat, val in skill.debuffs_formated:
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
        return self._vectorize_effects(
            is_applicable="is_buff",
            effects_attr="buffs",
            stat_types=self.all_buff_types,
            max_map=self.max_values_for_buffs,
        )

    @cached_property
    def skills_debuff_values(self) -> dict[CombatSkill, np.ndarray]:
        return self._vectorize_effects(
            is_applicable="is_debuff",
            effects_attr="debuffs",
            stat_types=self.all_debuff_types,
            max_map=self.max_values_for_debuffs,
        )
