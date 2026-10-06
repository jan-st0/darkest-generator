import cProfile
import pstats
import random
import sys
import time
from pathlib import Path
from typing import Sequence

from party_vectorizer.desire_vector import DVectorManager
from party_vectorizer.fitness import party_to_category_vector
from game_data_manager import GameDataManager
from data_model.hero_data_model import CombatSkill, Hero, HeroBuild
from data_model.party_data_model import Party
from data_model.trinket_data_model import Trinket


def generate_random_build(
    hero: Hero,
    rank: int,
    usable_generic_trinkets: Sequence[Trinket],
    class_trinkets_map: dict[str, list[Trinket]],
    trinket_chance: float = 0.8,
) -> HeroBuild:
    """Creates a random HeroBuild with 4 distinct combat skills and 0-2 legal trinkets."""
    # Darkest Dungeon loadouts require 4 skills (or all available if class has <= 4)
    k_skills = min(4, len(hero.combat_skills))
    selected_skills = tuple(random.sample(hero.combat_skills, k=k_skills))

    assigned_trinkets: list[Trinket] = []
    if random.random() < trinket_chance:
        hero_pool = class_trinkets_map.get(hero.class_name, []) + list(usable_generic_trinkets)
        num_trinkets = random.choice([1, 2])
        if len(hero_pool) >= num_trinkets:
            assigned_trinkets = random.sample(hero_pool, k=num_trinkets)

    return HeroBuild(
        hero=hero,
        rank=rank,
        skills=selected_skills,
        trinkets=tuple(assigned_trinkets),
    )


def generate_random_party(
    mgr: GameDataManager,
    usable_generic_trinkets: Sequence[Trinket],
    class_trinkets_map: dict[str, list[Trinket]],
) -> Party:
    """Samples 4 heroes and builds a valid Party instance."""
    # Allow duplicate classes or distinct classes across ranks 4 -> 1
    selected_heroes = random.choices(mgr.heroes, k=4)
    members = tuple(
        generate_random_build(
            hero=hero,
            rank=4 - idx,
            usable_generic_trinkets=usable_generic_trinkets,
            class_trinkets_map=class_trinkets_map,
        )
        for idx, hero in enumerate(selected_heroes)
    )
    return Party(members=members, man=mgr)


def run_ga_simulation(
    mgr: GameDataManager,
    dvec: DVectorManager,
    population_size: int = 100,
    generations: int = 15,
) -> None:
    """Simulates realistic GA lifecycle workload:

    - Instantiating individuals (movement permutation graph traversal + cached setups)
    - Full category vector heuristic scoring
    """
    usable_generic = [t for t in mgr.usable_trinkets if t.class_restriction is None]
    class_trinkets: dict[str, list[Trinket]] = {}
    for t in mgr.usable_trinkets:
        if t.class_restriction:
            class_trinkets.setdefault(t.class_restriction, []).append(t)

    print(
        f"Simulating GA: {generations} Generations x {population_size} Individuals "
        f"({generations * population_size} total evaluations)..."
    )

    total_evals = 0
    t0 = time.perf_counter()

    for gen in range(1, generations + 1):
        # Simulate generating offspring/population
        population = [
            generate_random_party(mgr, usable_generic, class_trinkets)
            for _ in range(population_size)
        ]

        # Evaluate fitness / category vectors for entire generation
        for party in population:
            vec = party_to_category_vector(party, mgr, dvec)
            # Lightweight check to prevent interpreter dead-code elimination
            if vec[18] < 0:
                print("Anomaly detected")
            total_evals += 1

    elapsed = time.perf_counter() - t0
    rate = total_evals / elapsed if elapsed > 0 else 0
    print(f"Finished {total_evals} evaluations in {elapsed:.3f}s ({rate:.1f} evals/sec).")


def main():
    print("Preheating GameDataManager and DVectorManager...")
    mgr = GameDataManager()
    dvec = DVectorManager()

    # Profiling parameters
    POPULATION_SIZE = 100
    GENERATIONS = 12

    print("\nStarting cProfile run...")
    profiler = cProfile.Profile()
    profiler.enable()

    run_ga_simulation(
        mgr=mgr,
        dvec=dvec,
        population_size=POPULATION_SIZE,
        generations=GENERATIONS,
    )

    profiler.disable()

    print("\n" + "=" * 80)
    print("PROFILING RESULTS: TOP 25 FUNCTIONS BY CUMULATIVE TIME")
    print("=" * 80)
    ps_cum = pstats.Stats(profiler).sort_stats(pstats.SortKey.CUMULATIVE)
    ps_cum.print_stats(25)

    print("\n" + "=" * 80)
    print("PROFILING RESULTS: TOP 20 FUNCTIONS BY INTERNAL TIME (tottime)")
    print("=" * 80)
    ps_tot = pstats.Stats(profiler).sort_stats(pstats.SortKey.TIME)
    ps_tot.print_stats(20)

    # Dump binary profile stats for snakeviz / viztracer / tuna inspection
    prof_path = Path(__file__).resolve().parent.parent / "ga_stress_test.prof"
    ps_cum.dump_stats(str(prof_path))
    print(f"\nFull binary profile dumped to: {prof_path}")
    print("Run `snakeviz ga_stress_test.prof` to visualize.")


if __name__ == "__main__":
    main()