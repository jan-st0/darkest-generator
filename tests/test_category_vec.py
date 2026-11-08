import pytest
from game_data_manager import GameDataManager
from game_utility import GameContext
from party_vectorizer.fitness import party_to_category_vector
from data_model.hero_data_model import HeroBuild
from data_model.party_data_model import Party


@pytest.fixture(scope="module")
def gman():
    return GameDataManager()


@pytest.fixture(scope="module")
def game_ctx(gman):
    return GameContext(gman)


def test_category_vector_untrinketed_party(gman, game_ctx):
    heroes = {h.class_name: h for h in gman.heroes}
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
    party = Party(members=(b4, b3, b2, b1), man=gman)
    vec = party_to_category_vector(party, game_ctx)

    assert len(vec) == 19
    assert vec[17] == 0.0
    assert vec[18] == 1.0


def test_category_vector_trinketed_party(gman, game_ctx):
    heroes = {h.class_name: h for h in gman.heroes}
    trinkets = gman.trinkets_by_name

    pd = heroes["Plague Doctor"]
    occ = heroes["Occultist"]
    bh = heroes["Bounty Hunter"]
    hel = heroes["Hellion"]

    pd_skills = tuple(s for s in pd.combat_skills if s.name in {
        "Plague Grenade", "Blinding Gas", "Battlefield Medicine", "Noxious Blast"
    })
    pd_trinkets = (
        trinkets["Blight Amulet"],
        trinkets["Quick Draw Charm"],
    )
    b4 = HeroBuild(hero=pd, rank=4, skills=pd_skills, trinkets=pd_trinkets)

    occ_skills = tuple(s for s in occ.combat_skills if s.name in {
        "Wyrd Reconstruction", "Vulnerability Hex", "Abyssal Artillery", "Daemon's Pull"
    })
    occ_trinkets = (
        trinkets["Chirurgeon's Charm"],
        trinkets["Solar Crown"],
    )
    b3 = HeroBuild(hero=occ, rank=3, skills=occ_skills, trinkets=occ_trinkets)

    bh_skills = tuple(s for s in bh.combat_skills if s.name in {
        "Collect Bounty", "Mark for Death", "Finish Him", "Flashbang"
    })
    bh_trinkets = (
        trinkets["Hunter's Talons"],
        trinkets["Sun Ring"],
    )
    b2 = HeroBuild(hero=bh, rank=2, skills=bh_skills, trinkets=bh_trinkets)

    hel_skills = tuple(s for s in hel.combat_skills if s.name in {
        "Wicked Hack", "Iron Swan", "If It Bleeds", "Bleed Out"
    })
    hel_trinkets = (
        trinkets["Heaven's Hairpin"],
        trinkets["Damage Stone"],
    )
    b1 = HeroBuild(hero=hel, rank=1, skills=hel_skills, trinkets=hel_trinkets)

    party = Party(members=(b4, b3, b2, b1), man=gman)
    vec = party_to_category_vector(party, game_ctx)

    assert len(vec) == 19
    assert vec[17] > 0.0
    assert party.has_mark is True
    assert vec[9] > 0.0
