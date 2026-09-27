import numpy as np
import pytest
from game_data_manager import GameDataManager
from desire_vector import (
    BUFF_STAT_ORDER,
    DEBUFF_STAT_ORDER,
    DVectorManager,
    calculate_buff_score,
    calculate_debuff_score,
    calculate_trinket_score,
    generate_default_debuff_vector,
    generate_default_desire_vectors,
)
from trinket_data_model import TrinketEvaluationContext


@pytest.fixture(scope="module")
def game_manager():
    return GameDataManager()


@pytest.fixture(scope="module")
def d_manager():
    return DVectorManager()


def test_default_vectors_generation_and_loading(game_manager, d_manager):
    # Verify debuff vector properties
    debuff_vec = generate_default_debuff_vector(game_manager)
    assert isinstance(debuff_vec, np.ndarray)
    assert debuff_vec.shape == (len(DEBUFF_STAT_ORDER),)
    assert debuff_vec.dtype == np.float64
    assert np.all(debuff_vec > 0.0)

    # Verify desire vectors properties
    desire_dict = generate_default_desire_vectors(game_manager)
    assert isinstance(desire_dict, dict)
    assert len(desire_dict) == 18
    for hero_name, vec in desire_dict.items():
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (len(BUFF_STAT_ORDER),)
        assert vec.dtype == np.float64
        assert np.all(vec >= 0.0)

    # Verify DVectorManager properties
    assert isinstance(d_manager.debuff, np.ndarray)
    assert d_manager.debuff.shape == (len(DEBUFF_STAT_ORDER),)
    assert len(d_manager.vec) == 18
    assert "Leper" in d_manager.vec
    assert "Vestal" in d_manager.vec
    assert "Plague Doctor" in d_manager.vec


def test_debuff_scoring(game_manager, d_manager):
    heroes = game_manager.heroes_by_name

    # Suppressing Fire debuffs ACC and CRIT across backline ranks
    arbalest = heroes["Arbalest"]
    suppress = next(s for s in arbalest.combat_skills if s.name == "Suppressing Fire")
    score_suppress = game_manager.evaluate_debuff_score(suppress, d_manager)
    assert score_suppress > 0.0

    # Target Whistle debuffs PROT
    houndmaster = heroes["Houndmaster"]
    whistle = next(s for s in houndmaster.combat_skills if s.name == "Target Whistle")
    score_whistle = game_manager.evaluate_debuff_score(whistle, d_manager)
    assert score_whistle > 0.0

    # Weakening Curse debuffs DMG and PROT
    occultist = heroes["Occultist"]
    curse = next(s for s in occultist.combat_skills if s.name == "Weakening Curse")
    score_curse = game_manager.evaluate_debuff_score(curse, d_manager)
    assert score_curse > 0.0

    # Non-debuff skill should score 0.0
    crusader = heroes["Crusader"]
    smite = next(s for s in crusader.combat_skills if s.name == "Smite")
    assert game_manager.evaluate_debuff_score(smite, d_manager) == 0.0


def test_buff_scoring_role_differentiation(game_manager, d_manager):
    heroes = game_manager.heroes_by_name
    jester = heroes["Jester"]
    leper = heroes["Leper"]
    antiquarian = heroes["Antiquarian"]

    # Battle Ballad buffs ACC, CRIT, SPD, and DMG
    ballad = next(s for s in jester.combat_skills if s.name == "Battle Ballad")

    # Leper has severe ACC/SPD penalties and massive damage scaling;
    # Antiquarian has low combat output and focuses on utility/dodge.
    # Therefore Leper must value Battle Ballad substantially more than Antiquarian.
    score_leper = game_manager.evaluate_buff_score(ballad, jester, [leper], d_manager)
    score_anti = game_manager.evaluate_buff_score(ballad, jester, [antiquarian], d_manager)

    assert score_leper > score_anti * 1.5, (
        f"Leper score ({score_leper:.2f}) should be significantly higher than Antiquarian ({score_anti:.2f})"
    )


def test_buff_scoring_self_and_negative_effects(game_manager, d_manager):
    heroes = game_manager.heroes_by_name
    leper = heroes["Leper"]

    # Revenge gives +DMG, +CRIT, +ACC, and -10 DODGE (self-debuff)
    revenge = next(s for s in leper.combat_skills if s.name == "Revenge")
    revenge_score = game_manager.evaluate_buff_score(revenge, leper, [leper], d_manager)

    # Net score should still be strongly positive for Leper because ACC & DMG outweigh Dodge loss
    assert revenge_score > 2.0

    # Non-buff skill produces 0.0
    chop = next(s for s in leper.combat_skills if s.name == "Chop")
    assert game_manager.evaluate_buff_score(chop, leper, [leper], d_manager) == 0.0


def test_trinket_scoring_class_restriction(game_manager, d_manager):
    heroes = game_manager.heroes_by_name
    pd = heroes["Plague Doctor"]
    crusader = heroes["Crusader"]

    # Blasphemous Vial is class restricted to Plague Doctor
    vial = game_manager.trinkets_by_name["Blasphemous Vial"]

    score_pd = game_manager.evaluate_trinket_score(vial, pd, d_manager=d_manager)
    score_crusader = game_manager.evaluate_trinket_score(vial, crusader, d_manager=d_manager)

    # Should give massive score to PD and 0.0 to Crusader
    assert score_pd > 3.0
    assert score_crusader == 0.0


def test_trinket_scoring_archetype_synergy(game_manager, d_manager):
    heroes = game_manager.heroes_by_name
    vestal = heroes["Vestal"]
    hwm = heroes["Highwayman"]

    # Junia's Head (+30% Healing Skills, +20% Stress)
    junia = game_manager.trinkets_by_name["Junia's Head"]

    score_vestal = game_manager.evaluate_trinket_score(junia, vestal, d_manager=d_manager)
    score_hwm = game_manager.evaluate_trinket_score(junia, hwm, d_manager=d_manager)

    # Vestal benefits from +30% healing which outweighs stress penalty.
    # Highwayman has no healing skills, so Junia's Head only inflicts stress penalty!
    assert score_vestal > 0.0
    assert score_hwm < 0.0


def test_trinket_scoring_torch_and_conditions(game_manager, d_manager):
    heroes = game_manager.heroes_by_name
    leper = heroes["Leper"]

    sun_ring = game_manager.trinkets_by_name["Sun Ring"]
    moon_ring = game_manager.trinkets_by_name["Moon Ring"]

    # Under >75 Torch assumption:
    # Sun Ring (+10% DMG, +5 ACC, +10% Stress) is active -> net positive
    # Moon Ring (requires Torch < 26) is inactive, so only +10% Stress penalty applies -> net negative
    score_sun = game_manager.evaluate_trinket_score(sun_ring, leper, d_manager=d_manager)
    score_moon = game_manager.evaluate_trinket_score(moon_ring, leper, d_manager=d_manager)

    assert score_sun > 0.0
    assert score_moon < 0.0


def test_trinket_ignored_and_item_exceptions(game_manager, d_manager):
    heroes = game_manager.heroes_by_name
    abom = heroes["Abomination"]

    # Ignored trinkets return 0.0
    baron = game_manager.trinkets_by_name["Baron's Lash"]
    assert game_manager.evaluate_trinket_score(baron, abom, d_manager=d_manager) == 0.0

    # Restraining Padlock: custom item exception mitigating Abomination transformation stress
    padlock = game_manager.trinkets_by_name["Restraining Padlock"]
    score_padlock = game_manager.evaluate_trinket_score(padlock, abom, d_manager=d_manager)
    assert score_padlock > 0.0


def test_utility_trinkets(game_manager, d_manager):
    heroes = game_manager.heroes_by_name
    houndmaster = heroes["Houndmaster"]

    # Scouting Whistle gives scouting chance and bonus vs beasts
    whistle_trinket = game_manager.trinkets_by_name["Scouting Whistle"]
    score = game_manager.evaluate_trinket_score(whistle_trinket, houndmaster, d_manager=d_manager)
    assert score > 0.0
