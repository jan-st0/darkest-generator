import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from game_data_manager import GameDataManager
from trinket_data_model import TrinketEvaluationContext
from trinket_evaluator import (
    ALL_IGNORED_TRINKETS,
    IGNORED_COLOR_OF_MADNESS_TRINKETS,
    IGNORED_CRIMSON_COURT_TRINKETS,
    UTILITY_STATS,
)


def main() -> None:
    man = GameDataManager()

    print("=" * 80)
    print("TRINKET FILTERING & EXCLUSION SUMMARY")
    print("=" * 80)
    print(f"Total trinkets loaded: {len(man.trinkets)}")
    print(f"Ignored Crimson Court trinkets ({len(IGNORED_CRIMSON_COURT_TRINKETS)}): {sorted(IGNORED_CRIMSON_COURT_TRINKETS)}")
    print(f"Ignored Color of Madness trinkets ({len(IGNORED_COLOR_OF_MADNESS_TRINKETS)}): {sorted(IGNORED_COLOR_OF_MADNESS_TRINKETS)}")
    print(f"Total excluded trinkets: {len(ALL_IGNORED_TRINKETS)}")
    print(f"Total usable trinkets for heuristic: {len(man.usable_trinkets)}")
    print()

    print("=" * 80)
    print("GLOBAL UTILITY STATS (MIN-MAX NORMALIZATION CANDIDATES)")
    print("=" * 80)
    for stat, max_val in man.max_values_for_utility_stats.items():
        print(f"  {stat:30s} -> Max observed: {max_val}")
    print()

    print("=" * 80)
    print("ITEM EXCEPTION & SPECIAL CONDITION PARSING SAMPLES")
    print("=" * 80)

    sample_items = [
        ("Sun Ring", TrinketEvaluationContext()),
        ("Moon Ring", TrinketEvaluationContext()),
        ("Camper's Helmet", TrinketEvaluationContext()),
        ("Sickening Satchel (no blight)", TrinketEvaluationContext(has_blight_skills=False)),
        ("Sickening Satchel (with blight)", TrinketEvaluationContext(has_blight_skills=True)),
        ("Vvulf's Tassle (no mark theme)", TrinketEvaluationContext(team_has_mark=False)),
        ("Vvulf's Tassle (with mark theme)", TrinketEvaluationContext(team_has_mark=True)),
        ("Restraining Padlock", TrinketEvaluationContext()),
        ("Second Place Trophy", TrinketEvaluationContext()),
        ("Acidic Husk Ichor", TrinketEvaluationContext()),
        ("Topshelf Tonic", TrinketEvaluationContext()),
        ("Dirge For The Devoured", TrinketEvaluationContext()),
        ("Focus Ring", TrinketEvaluationContext()),
    ]

    for item_desc, ctx in sample_items:
        clean_name = item_desc.split(" (")[0]
        trinket = man.trinkets_by_name.get(clean_name)
        if not trinket:
            continue
        eval_stats = man.evaluate_trinket(trinket, ctx)
        print(f"[{item_desc}]")
        print(f"  Raw effects: {[e.raw for e in trinket.effects]}")
        print(f"  Evaluated stats: {eval_stats}")
        print()

    print("=" * 80)
    print("SAMPLE EVALUATION ACROSS HERO CONTEXTS (e.g. Melee vs Ranged)")
    print("=" * 80)
    wounding_helmet = man.trinkets_by_name.get("Wounding Helmet")
    if wounding_helmet:
        melee_ctx = TrinketEvaluationContext(has_melee_skills=True, has_ranged_skills=False)
        ranged_ctx = TrinketEvaluationContext(has_melee_skills=False, has_ranged_skills=True)
        print("Wounding Helmet with Melee hero:", man.evaluate_trinket(wounding_helmet, melee_ctx))
        print("Wounding Helmet with Ranged hero:", man.evaluate_trinket(wounding_helmet, ranged_ctx))
        print()


if __name__ == "__main__":
    main()
