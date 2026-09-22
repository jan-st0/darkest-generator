from game_data_manager import GameDataManager
from trinket_data_model import (
    Trinket,
    TrinketEffect,
    TrinketEvaluationContext,
)
from trinket_evaluator import (
    ALL_IGNORED_TRINKETS,
    IGNORED_COLOR_OF_MADNESS_TRINKETS,
    IGNORED_CRIMSON_COURT_TRINKETS,
    evaluate_trinket_stats,
    is_trinket_ignored,
)


def test_trinket_data_models():
    eff = TrinketEffect(stat="ACC", modifier=10, unit=None, condition=None, raw="+10 ACC")
    assert eff.stat == "ACC"
    assert eff.modifier == 10
    assert not eff.is_torch_effect()
    assert not eff.is_position_dependent()
    assert not eff.is_food_effect()

    torch_eff = TrinketEffect(stat="DMG", modifier=15, unit="%", condition="if Torch > 75", raw="+15% DMG if Torch > 75")
    assert torch_eff.is_torch_effect()

    food_eff = TrinketEffect(stat="Food Consumed", modifier=100, unit="%", condition=None, raw="+100% Food Consumed")
    assert food_eff.is_food_effect()

    trinket = Trinket(
        name="Test Charm",
        rarity="Common",
        category="Generic",
        effects=(eff,),
        class_restriction=None,
    )
    assert trinket.name == "Test Charm"
    assert not trinket.is_crimson_court
    assert not trinket.is_crystalline


def test_ignored_trinkets_count():
    assert len(IGNORED_CRIMSON_COURT_TRINKETS) == 3
    assert len(IGNORED_COLOR_OF_MADNESS_TRINKETS) == 16
    assert len(ALL_IGNORED_TRINKETS) == 19


def test_manager_trinket_filtering():
    mgr = GameDataManager()
    total_trinkets = len(mgr.trinkets)
    usable_trinkets = len(mgr.usable_trinkets)
    assert total_trinkets == 286
    # 19 ignored trinkets
    assert usable_trinkets == 286 - 19

    # Specific ignored item check
    assert is_trinket_ignored("Baron's Lash")
    assert is_trinket_ignored("Lens of the Comet")
    assert not is_trinket_ignored("Blasphemous Vial")


def test_item_exceptions():
    mgr = GameDataManager()

    # Camper's Helmet: ignore stress heal while camping
    camper = mgr.trinkets_by_name["Camper's Helmet"]
    stats_camper = evaluate_trinket_stats(camper)
    assert "Stress Heal Received" not in stats_camper
    assert "Scouting Chance" in stats_camper

    # Vvulf's Tassle: ignore CRIT vs size 2+
    vvulf = mgr.trinkets_by_name["Vvulf's Tassle"]
    # With mark theme
    ctx_mark = TrinketEvaluationContext(team_has_mark=True)
    stats_vvulf_mark = evaluate_trinket_stats(vvulf, ctx_mark)
    assert "CRIT" not in stats_vvulf_mark
    assert stats_vvulf_mark["DMG"] == 20 * 0.7  # 14.0
    assert stats_vvulf_mark["ACC"] == 10 * 0.7  # 7.0

    # Without mark theme
    ctx_no_mark = TrinketEvaluationContext(team_has_mark=False)
    stats_vvulf_nomark = evaluate_trinket_stats(vvulf, ctx_no_mark)
    assert stats_vvulf_nomark.get("DMG", 0.0) == 0.0
    assert stats_vvulf_nomark.get("ACC", 0.0) == 0.0

    # Acidic Husk Ichor: ignore vs Husk
    ichor = mgr.trinkets_by_name["Acidic Husk Ichor"]
    stats_ichor = evaluate_trinket_stats(ichor)
    assert "Bleed Skill Chance" not in stats_ichor
    assert stats_ichor["MAX HP"] == -25.0
    assert stats_ichor["DMG"] == 30.0

    # Topshelf Tonic: ignore Herbs
    tonic = mgr.trinkets_by_name["Topshelf Tonic"]
    stats_tonic = evaluate_trinket_stats(tonic)
    assert "DODGE" not in stats_tonic
    assert stats_tonic["SPD"] == 3.0

    # Dirge For The Devoured: ignore Laudanum
    dirge = mgr.trinkets_by_name["Dirge For The Devoured"]
    stats_dirge = evaluate_trinket_stats(dirge)
    assert stats_dirge["Stress Skills"] == 25.0
    assert stats_dirge["Stress"] == 10.0
    assert "DMG" not in stats_dirge

    # Sickening Satchel: 0 if no blight, 0.5 * 20 = 10 if blight
    satchel = mgr.trinkets_by_name["Sickening Satchel"]
    assert evaluate_trinket_stats(satchel, TrinketEvaluationContext(has_blight_skills=False)).get("DMG", 0.0) == 0.0
    assert evaluate_trinket_stats(satchel, TrinketEvaluationContext(has_blight_skills=True))["DMG"] == 10.0

    # Restraining Padlock: custom fixed value
    padlock = mgr.trinkets_by_name["Restraining Padlock"]
    stats_padlock = evaluate_trinket_stats(padlock)
    assert stats_padlock["Transformation Stress"] == -40.0
    assert stats_padlock["Stress Inflicted on Party"] == -40.0


def test_torch_conditions():
    mgr = GameDataManager()
    sun_ring = mgr.trinkets_by_name["Sun Ring"]
    moon_ring = mgr.trinkets_by_name["Moon Ring"]

    # Sun Ring requires Torch > 75 (assumed active)
    sun_stats = evaluate_trinket_stats(sun_ring)
    assert sun_stats["DMG"] == 10.0
    assert sun_stats["ACC"] == 5.0
    assert sun_stats["Stress"] == 10.0

    # Moon Ring requires Torch < 26 (assumed inactive)
    moon_stats = evaluate_trinket_stats(moon_ring)
    assert moon_stats.get("DMG", 0.0) == 0.0
    assert moon_stats.get("ACC", 0.0) == 0.0
    assert moon_stats["Stress"] == 10.0  # unconditional penalty applies


if __name__ == "__main__":
    test_trinket_data_models()
    test_ignored_trinkets_count()
    test_manager_trinket_filtering()
    test_item_exceptions()
    test_torch_conditions()
    print("ALL TRINKET MODEL & EVALUATION TESTS PASSED!")
