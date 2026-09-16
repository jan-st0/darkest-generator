from typing import Any, Union

from data_model import (
    BaseStatsLvl0,
    BaseStatsLvl6,
    BuffDebuffEffect,
    CampingSkill,
    CombatSkill,
    DotEffect,
    HealEffect,
    Hero,
    MarkEffect,
    Metadata,
    MovementEffect,
    SkillCombatStats,
    StressHealEffect,
    StunEffect,
    Trinket,
    TrinketEffect,
    TrinketRef,
    TrinketSet,
)    


def parse_buff_debuff(data: dict[str, Any]) -> BuffDebuffEffect:
    return BuffDebuffEffect(**data)

def parse_heal(data: Union[dict[str, Any], list[dict[str, Any]]]) -> tuple[HealEffect, ...]:
    if isinstance(data, list):
        return tuple(HealEffect(**h) for h in data)
    if isinstance(data, dict):
        if not data.get("has_heal", True):
            return ()
        clean_data = {k: v for k, v in data.items() if k != "has_heal"}
        return (HealEffect(**clean_data),)
    return ()

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
        heal=parse_heal(data.get("heal", [])),
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