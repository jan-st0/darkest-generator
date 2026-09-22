from typing import Optional
from trinket_data_model import Trinket, TrinketEffect, TrinketEvaluationContext


IGNORED_CRIMSON_COURT_TRINKETS: frozenset[str] = frozenset({
    "Viscount's Spices",
    "Baron's Lash",
    "Countess' Fan",
})

IGNORED_COLOR_OF_MADNESS_TRINKETS: frozenset[str] = frozenset({
    "Lens of the Comet",
    "Crystal Pendant",
    "Cluster Pendant",
    "Coat Of Many Colors",
    "Miller's Pipe",
    "Smoking Skull",
    "Keening Bolts",
    "Non-Euclidean Hilt",
    "Petrified Skull",
    "Petrified Amulet",
    "Heretical Passage",
    "Prismatic Heart Crystal",
    "Thirsting Blade",
    "Huskfang Whistle",
    "Mirror Shield",
    "Icosahedric Musket Balls",
})

ALL_IGNORED_TRINKETS: frozenset[str] = IGNORED_CRIMSON_COURT_TRINKETS | IGNORED_COLOR_OF_MADNESS_TRINKETS

UTILITY_STATS: frozenset[str] = frozenset({
    "Scouting Chance",
    "Scouting",
    "Trap Disarm Chance",
    "Chance Monsters Surprised",
    "Surprise Chance",
    "Chance Party Surprised",
})

IGNORED_STATS: frozenset[str] = frozenset({
    "Food Consumed",
    "Resolve XP",
    "Shards Given",
    "Random Target",
    "Random Target Chance",
    "Self: Lose 5 HP",
    "Self: Stress +3 (25% chance)",
    "Healing Skills Camping",
    "Stress Skills Camping",
    "Stress Camping",
    "-2% Stress (2 Battles)",
    "ACC (2 Battles)",
    "Stress -2",
})

ENEMY_TYPE_CONDITIONS: frozenset[str] = frozenset({
    "vs Beast",
    "vs Bleeding",
    "vs Blighted",
    "vs Bloodsuckers",
    "vs Eldritch",
    "vs Fanatic",
    "vs Human",
    "vs Husk",
    "vs Husk/Eldritch",
    "vs Miller",
    "vs Stonework",
    "vs Thing",
    "vs Unholy",
    "vs size 2+",
    "when attacked by Eldritch",
    "when attacked by Husk",
})


def is_trinket_ignored(name: str) -> bool:
    """Checks whether a trinket should be completely skipped in heuristic evaluation."""
    return name in ALL_IGNORED_TRINKETS


def preprocess_trinket_effects(trinket: Trinket) -> tuple[TrinketEffect, ...]:
    """Filters or modifies raw trinket effects according to specific item exceptions in diagram.md.

    Exceptions handled:
    - Camper's Helmet: Ignore stress heal effect while camping.
    - Sickening Satchel: handled in scaling (+20% DMG vs Blighted).
    - Vvulf's Tassle: Ignore +5% CRIT vs size 2+.
    - Second Place Trophy: Ignore Camp heal bonus (Healing Skills Camping).
    - Acidic Husk Ichor: Ignore vs Husk effect.
    - Topshelf Tonic: Ignore +15 DODGE with Herbs.
    - Dirge For The Devoured: Ignore +25% DMG with Laudanum.
    - Food effects: Ignored.
    """
    processed: list[TrinketEffect] = []
    name = trinket.name

    for eff in trinket.effects:
        # Ignore food effects
        if eff.is_food_effect():
            continue

        # Ignore stats explicitly marked to omit
        if eff.stat in IGNORED_STATS:
            continue

        # Item-specific exception checks
        if name == "Camper's Helmet" and eff.condition == "while Camping":
            continue

        if name == "Vvulf's Tassle" and eff.condition == "vs size 2+":
            continue

        if name == "Acidic Husk Ichor" and eff.condition == "vs Husk":
            continue

        if name == "Topshelf Tonic" and eff.condition == "if Medicinal Herbs":
            continue

        if name == "Dirge For The Devoured" and eff.condition == "if Laudanum in inventory":
            continue

        processed.append(eff)

    return tuple(processed)


def calculate_effect_scaling(
    effect: TrinketEffect,
    trinket_name: str,
    context: Optional[TrinketEvaluationContext] = None,
) -> float:
    """Calculates scaling multiplier [0.0, 1.0] for a trinket effect given the hero evaluation context.

    Follows rules from diagram.md:
    - Torch level (>75 Torch assumed): Torch > 75 -> 1.0, Torch < X -> 0.0.
    - Ranged / Melee conditions: 0.0 if hero lacks required skill type.
    - Round-based conditions: On R1 -> 0.25, After R1 -> 0.75.
    - Hero position: Checks if current rank matches position condition, discounted if movement unstable.
    - On Death's Door: Heavy penalty / minimal scaling -> 0.05.
    - HP below thresholds: Penalty / lower scaling -> 0.2.
    - vs Marked: 0.7 if team mark theme, else 0.0.
    - Enemy type conditions: Lower scaling (e.g. 0.25) to normalize expected value across encounters.
    - Sickening Satchel: 0.0 if hero has no blight skill, else 0.5.
    """
    if context is None:
        context = TrinketEvaluationContext()

    cond = effect.condition
    stat = effect.stat

    # Specific item: Sickening Satchel
    if trinket_name == "Sickening Satchel":
        if not context.has_blight_skills:
            return 0.0
        return 0.5  # Lower DMG scaling as in diagram

    # Check melee vs ranged skill availability
    if "melee" in stat.lower():
        if not context.has_melee_skills:
            return 0.0
    if "ranged" in stat.lower():
        if not context.has_ranged_skills:
            return 0.0

    # If no condition, effect is fully active
    if not cond:
        # Check position in stat name, e.g. "DODGE in pos 1", "SPD in pos 1"
        if "pos 1" in stat.lower():
            if context.hero_rank != 1:
                return 0.0
            return 1.0 if context.is_movement_stable else 0.6
        return 1.0

    cond_clean = cond.strip()

    # 1. Torch level (>75 Torch assumed)
    if "torch" in cond_clean.lower():
        # Active only if requires high torch (Torch > 50, Torch > 51, Torch > 75)
        if any(k in cond_clean for k in ("Torch above", "Torch >")):
            return 1.0
        # If requires low torch (Torch < 50, Torch < 75, Torch below 25/50/51)
        return 0.0

    # 2. Position conditions (e.g. "if in position 1", "if in position 2", "if in position 4")
    if "position" in cond_clean.lower() or "pos " in cond_clean.lower():
        target_pos = None
        for p in (1, 2, 3, 4):
            if str(p) in cond_clean:
                target_pos = p
                break
        if target_pos is not None:
            if context.hero_rank != target_pos:
                return 0.0
            return 1.0 if context.is_movement_stable else 0.6

    # 3. Round-based conditions
    if cond_clean == "on First Round":
        return 0.25
    if "after first round" in cond_clean.lower():
        return 0.75

    # 4. On Death's Door
    if "death's door" in cond_clean.lower():
        return 0.05

    # 5. HP threshold conditions
    if "hp <" in cond_clean.lower() or "hp below" in cond_clean.lower():
        return 0.2
    if "hp >" in cond_clean.lower() or "hp above" in cond_clean.lower():
        return 0.85

    # 6. Mark condition
    if cond_clean == "vs Marked":
        return 0.7 if context.team_has_mark else 0.0

    if cond_clean == "vs Marked/Stunned/Bleeding":
        # Crimson Court Bounty Hunter bonus
        return 0.8 if (context.team_has_mark or context.has_bleed_skills) else 0.4

    # 7. Enemy type condition (normalize expected value across random encounters)
    if cond_clean in ENEMY_TYPE_CONDITIONS or "vs " in cond_clean:
        if cond_clean == "vs Bleeding":
            return 0.75 if context.has_bleed_skills else 0.2
        if cond_clean == "vs Blighted":
            return 0.75 if context.has_blight_skills else 0.2
        return 0.25

    # Other conditions (e.g. while Guarding, on Transform, if Bloodlust, if Bandage, etc.)
    # Default to 0.0 or low scaling if situational
    if cond_clean in {"if Bloodlust", "if Wasting", "if has Crimson Curse", "while Guarding"}:
        return 0.2
    if cond_clean == "on Transform":
        return 1.0  # Relevant for Abomination

    return 1.0


def evaluate_trinket_stats(
    trinket: Trinket,
    context: Optional[TrinketEvaluationContext] = None,
) -> dict[str, float]:
    """Computes effective numerical stat modifiers of a trinket taking into account exceptions and conditions.

    Returns a mapping of normalized stat name -> effective numeric modifier.
    """
    if context is None:
        context = TrinketEvaluationContext()

    if is_trinket_ignored(trinket.name):
        return {}

    # Restraining Padlock custom fixed value
    if trinket.name == "Restraining Padlock":
        # Custom evaluation: high stress mitigation bonus for Abomination
        return {"Transformation Stress": -40.0, "Stress Inflicted on Party": -40.0}

    effects = preprocess_trinket_effects(trinket)
    stat_totals: dict[str, float] = {}

    for eff in effects:
        if eff.modifier is None:
            continue

        scale = calculate_effect_scaling(eff, trinket.name, context)
        if scale <= 0.0:
            continue

        effective_val = eff.modifier * scale
        # Normalize stat names where position or skill-type was part of stat
        stat_name = eff.stat
        if " in pos 1" in stat_name:
            stat_name = stat_name.replace(" in pos 1", "").strip()

        stat_totals[stat_name] = stat_totals.get(stat_name, 0.0) + effective_val

    return stat_totals
