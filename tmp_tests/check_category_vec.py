import sys
from pathlib import Path

# Ensure repo root is in module search path

from party_vectorizer.desire_vector import DVectorManager
from party_vectorizer.fitness import party_to_category_vector
from game_data_manager import GameDataManager
from data_model.hero_data_model import HeroBuild
from data_model.party_data_model import Party


def build_untrinketed_party(mgr: GameDataManager) -> Party:
    """Builds Team 1 (Vestal / Jester / Highwayman / Crusader) without trinkets."""
    heroes = {h.class_name: h for h in mgr.heroes}

    vestal = heroes["Vestal"]
    jester = heroes["Jester"]
    hwm = heroes["Highwayman"]
    crusader = heroes["Crusader"]

    b4 = HeroBuild(
        hero=vestal,
        rank=4,
        skills=tuple(s for s in vestal.combat_skills if s.name in {
            "Divine Grace", "Divine Comfort", "Dazzling Light", "Judgement"
        }),
    )
    b3 = HeroBuild(
        hero=jester,
        rank=3,
        skills=tuple(s for s in jester.combat_skills if s.name in {
            "Battle Ballad", "Inspiring Tune", "Harvest", "Dirk Stab"
        }),
    )
    b2 = HeroBuild(
        hero=hwm,
        rank=2,
        skills=tuple(s for s in hwm.combat_skills if s.name in {
            "Duelist's Advance", "Point Blank Shot", "Pistol Shot", "Open Vein"
        }),
    )
    b1 = HeroBuild(
        hero=crusader,
        rank=1,
        skills=tuple(s for s in crusader.combat_skills if s.name in {
            "Smite", "Stunning Blow", "Holy Lance", "Inspiring Cry"
        }),
    )

    party = Party(members=(b4, b3, b2, b1), man=mgr)

    return party


def build_trinketed_party(mgr: GameDataManager) -> Party:
    """Builds Team 2 (Plague Doctor / Occultist / Bounty Hunter / Hellion) equipped with trinkets."""
    heroes = {h.class_name: h for h in mgr.heroes}
    trinkets = mgr.trinkets_by_name

    pd = heroes["Plague Doctor"]
    occ = heroes["Occultist"]
    bh = heroes["Bounty Hunter"]
    hel = heroes["Hellion"]

    # Rank 4: Plague Doctor (Blight + Stun + Disorienting Blast)
    pd_skills = tuple(s for s in pd.combat_skills if s.name in {
        "Plague Grenade", "Blinding Gas", "Battlefield Medicine", "Noxious Blast"
    })
    pd_trinkets = (
        trinkets["Blight Amulet"],
        trinkets["Quick Draw Charm"],
    )
    b4 = HeroBuild(hero=pd, rank=4, skills=pd_skills, trinkets=pd_trinkets)

    # Rank 3: Occultist (Heal + Vulnerability Hex / Mark + Abyssal Artillery)
    occ_skills = tuple(s for s in occ.combat_skills if s.name in {
        "Wyrd Reconstruction", "Vulnerability Hex", "Abyssal Artillery", "Daemon's Pull"
    })
    occ_trinkets = (
        trinkets["Chirurgeon's Charm"],
        trinkets["Solar Crown"],
    )
    b3 = HeroBuild(hero=occ, rank=3, skills=occ_skills, trinkets=occ_trinkets)

    # Rank 2: Bounty Hunter (Mark consumer / Uppercut / Finish Him)
    bh_skills = tuple(s for s in bh.combat_skills if s.name in {
        "Collect Bounty", "Mark for Death", "Finish Him", "Flashbang"
    })
    bh_trinkets = (
        trinkets["Hunter's Talons"],
        trinkets["Sun Ring"],
    )
    b2 = HeroBuild(hero=bh, rank=2, skills=bh_skills, trinkets=bh_trinkets)

    # Rank 1: Hellion (Damage / Iron Swan / Bleed Out / Wicked Hack)
    hel_skills = tuple(s for s in hel.combat_skills if s.name in {
        "Wicked Hack", "Iron Swan", "If It Bleeds", "Bleed Out"
    })
    hel_trinkets = (
        trinkets["Heaven's Hairpin"],
        trinkets["Damage Stone"],
    )
    b1 = HeroBuild(hero=hel, rank=1, skills=hel_skills, trinkets=hel_trinkets)

    party = Party(members=(b4, b3, b2, b1), man=mgr)

    return party


def print_comparison_table(labels: list[str], vec_a, vec_b, title_a: str, title_b: str):
    print("=" * 86)
    print(f"{'CATEGORY':<44} | {title_a:^18} | {title_b:^18}")
    print("=" * 86)
    for label, val_a, val_b in zip(labels, vec_a, vec_b):
        print(f"{label:<44} | {val_a:>18.4f} | {val_b:>18.4f}")
    print("=" * 86)


def main():
    print("Initializing GameDataManager and DVectorManager...")
    mgr = GameDataManager()
    dvec = DVectorManager()

    category_labels = [
        "0. Enemy Debuffs (unscaled dot product)",
        "1. Normalized Party Healing",
        "2. Ally/Party/Self Buff Score",
        "3. Normalized Self Healing",
        "4. Normalized Raw DPS",
        "5. Normalized Backline Reach DMG",
        "6. vs Stunned skill present",
        "7. vs Stunned synergy (present & team stuns)",
        "8. vs Marked skill present",
        "9. vs Marked synergy (present & team marks)",
        "10. Normalized Bleed Output",
        "11. Normalized Blight Output",
        "12. Normalized Stun Coverage",
        "13. Enemy R1 Target Reachability",
        "14. Enemy R2 Target Reachability",
        "15. Enemy R3 Target Reachability",
        "16. Enemy R4 Target Reachability",
        "17. Trinket Valuation Score",
        "18. Active Skill Completeness (fraction of 16)",
    ]

    print("\n--- Team 1: Classic Ruins Comp (No Trinkets) ---")
    party1 = build_untrinketed_party(mgr)
    for m in party1.members:
        print(f"  Rank {m.rank} [{m.name}]: {[s.name for s in m.active_skills]}")
    vec1 = party_to_category_vector(party1, mgr, dvec)

    print("\n--- Team 2: Mark & DoT Comp (With Trinkets) ---")
    party2 = build_trinketed_party(mgr)
    for m in party2.members:
        t_names = [t.name for t in m.trinkets]
        print(f"  Rank {m.rank} [{m.name}]: {[s.name for s in m.active_skills]} | Trinkets: {t_names}")
    vec2 = party_to_category_vector(party2, mgr, dvec)

    print("\n\nOUTPUT VISUALIZATION COMPARISON:")
    print_comparison_table(
        labels=category_labels,
        vec_a=vec1,
        vec_b=vec2,
        title_a="Team 1 (No Trinkets)",
        title_b="Team 2 (Trinkets)",
    )

    # Sanity checks for trinkets and mark synergy
    print(f"\nVerification:")
    print(f"  Team 1 Trinket Score: {vec1[17]:.4f} (Expected: 0.0000)")
    print(f"  Team 2 Trinket Score: {vec2[17]:.4f} (Expected: > 0.0000)")
    print(f"  Team 2 vs Marked Synergy: {vec2[9]:.4f} (Applies mark={party2.has_mark})")


if __name__ == "__main__":
    main()