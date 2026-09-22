"""Unified re-export module for hero and trinket data models.

Provides backward compatibility for existing code importing from data_model.
"""

from hero_data_model import (
    BaseStatsLvl0,
    BaseStatsLvl6,
    BuffDebuffEffect,
    CampingSkill,
    CombatSkill,
    DotEffect,
    HealEffect,
    Hero,
    HeroBuild,
    MarkEffect,
    Metadata,
    MovementEffect,
    Party,
    SkillCombatStats,
    StressHealEffect,
    StunEffect,
)
from trinket_data_model import (
    Trinket,
    TrinketEffect,
    TrinketEvaluationContext,
    TrinketRef,
    TrinketSet,
)

__all__ = [
    "Metadata",
    "BaseStatsLvl0",
    "BaseStatsLvl6",
    "SkillCombatStats",
    "StunEffect",
    "DotEffect",
    "MarkEffect",
    "HealEffect",
    "StressHealEffect",
    "MovementEffect",
    "BuffDebuffEffect",
    "CombatSkill",
    "CampingSkill",
    "Hero",
    "HeroBuild",
    "Party",
    "TrinketEffect",
    "Trinket",
    "TrinketRef",
    "TrinketSet",
    "TrinketEvaluationContext",
]
