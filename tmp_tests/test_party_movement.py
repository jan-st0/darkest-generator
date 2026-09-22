import pytest

from game_data_manager import GameDataManager
from hero_data_model import HeroBuild, Party


@pytest.fixture(scope="module")
def mgr():
    return GameDataManager()


def get_hero(mgr: GameDataManager, name: str):
    return next(h for h in mgr.heroes if h.class_name == name)


def get_skill(hero, name: str):
    return next(s for s in hero.combat_skills if s.name == name)


def test_party_size_invariance(mgr):
    crusader = get_hero(mgr, "Crusader")
    vestal = get_hero(mgr, "Vestal")
    holy_lance = get_skill(crusader, "Holy Lance")
    mace = get_skill(vestal, "Mace Bash")

    members = (
        HeroBuild(hero=crusader, rank=4, skills=(holy_lance,)),
        HeroBuild(hero=vestal, rank=3, skills=(mace,)),
        HeroBuild(hero=vestal, rank=2, skills=(mace,)),
        HeroBuild(hero=vestal, rank=1, skills=(mace,)),
    )
    party = Party(members=members)
    hero_positions = {hero: {4 - i} for i, hero in enumerate(party.members)}

    party._traverse_permutations(hero_positions, party.members, 1)

    for hero, positions in hero_positions.items():
        assert len(positions) <= 4


def test_backline_advance_indexing(mgr):
    crusader = get_hero(mgr, "Crusader")
    vestal = get_hero(mgr, "Vestal")
    holy_lance = get_skill(crusader, "Holy Lance")
    mace = get_skill(vestal, "Mace Bash")

    c4 = HeroBuild(hero=crusader, rank=4, skills=(holy_lance,))
    members = (
        c4,
        HeroBuild(hero=vestal, rank=3, skills=(mace,)),
        HeroBuild(hero=vestal, rank=2, skills=(mace,)),
        HeroBuild(hero=vestal, rank=1, skills=(mace,)),
    )
    party = Party(members=members)
    party.set_active_skills()

    assert holy_lance in c4.active_skills


def test_valid_rank_bounds(mgr):
    sb = get_hero(mgr, "Shieldbreaker")
    vestal = get_hero(mgr, "Vestal")
    pierce = get_skill(sb, "Pierce")
    mace = get_skill(vestal, "Mace Bash")

    members = (
        HeroBuild(hero=vestal, rank=4, skills=(mace,)),
        HeroBuild(hero=vestal, rank=3, skills=(mace,)),
        HeroBuild(hero=vestal, rank=2, skills=(mace,)),
        HeroBuild(hero=sb, rank=1, skills=(pierce,)),
    )
    party = Party(members=members)
    hero_positions = {hero: {4 - i} for i, hero in enumerate(party.members)}

    party._traverse_permutations(hero_positions, party.members, 1)

    for hero, positions in hero_positions.items():
        assert positions.issubset({1, 2, 3, 4})


def test_multi_rank_advance_reach(mgr):
    gr = get_hero(mgr, "Grave Robber")
    vestal = get_hero(mgr, "Vestal")
    lunge = get_skill(gr, "Lunge")
    mace = get_skill(vestal, "Mace Bash")

    gr3 = HeroBuild(hero=gr, rank=3, skills=(lunge,))
    members = (
        HeroBuild(hero=vestal, rank=4, skills=(mace,)),
        gr3,
        HeroBuild(hero=vestal, rank=2, skills=(mace,)),
        HeroBuild(hero=vestal, rank=1, skills=(mace,)),
    )
    party = Party(members=members)
    hero_positions = {hero: {4 - i} for i, hero in enumerate(party.members)}

    party._traverse_permutations(hero_positions, party.members, 1)

    assert 1 in hero_positions[gr3]


def test_launch_rank_prerequisite_enforcement(mgr):
    hwm = get_hero(mgr, "Highwayman")
    vestal = get_hero(mgr, "Vestal")
    pbs = get_skill(hwm, "Point Blank Shot")
    mace = get_skill(vestal, "Mace Bash")

    h2 = HeroBuild(hero=hwm, rank=2, skills=(pbs,))
    members = (
        HeroBuild(hero=vestal, rank=4, skills=(mace,)),
        HeroBuild(hero=vestal, rank=3, skills=(mace,)),
        h2,
        HeroBuild(hero=vestal, rank=1, skills=(mace,)),
    )
    party = Party(members=members)
    party.set_active_skills()

    assert pbs not in h2.active_skills


def test_highwayman_dance_convergence(mgr):
    hwm = get_hero(mgr, "Highwayman")
    vestal = get_hero(mgr, "Vestal")
    da = get_skill(hwm, "Duelist's Advance")
    pbs = get_skill(hwm, "Point Blank Shot")
    mace = get_skill(vestal, "Mace Bash")

    h2 = HeroBuild(hero=hwm, rank=2, skills=(da, pbs))
    members = (
        HeroBuild(hero=vestal, rank=4, skills=(mace,)),
        HeroBuild(hero=vestal, rank=3, skills=(mace,)),
        h2,
        HeroBuild(hero=vestal, rank=1, skills=(mace,)),
    )
    party = Party(members=members)
    party.set_active_skills()

    assert pbs in h2.active_skills
    assert da in h2.active_skills


def test_displacement_cascade_and_passive_unlock(mgr):
    gr = get_hero(mgr, "Grave Robber")
    vestal = get_hero(mgr, "Vestal")
    lunge = get_skill(gr, "Lunge")
    divine_grace = get_skill(vestal, "Divine Grace")
    mace = get_skill(vestal, "Mace Bash")

    v2 = HeroBuild(hero=vestal, rank=2, skills=(divine_grace, mace))
    gr4 = HeroBuild(hero=gr, rank=4, skills=(lunge,))
    members = (
        gr4,
        HeroBuild(hero=vestal, rank=3, skills=(mace,)),
        v2,
        HeroBuild(hero=vestal, rank=1, skills=(mace,)),
    )
    party = Party(members=members)
    party.set_active_skills()

    assert divine_grace in v2.active_skills

def test_boundary_clamping_saturation(mgr):
    sb = get_hero(mgr, "Shieldbreaker")
    vestal = get_hero(mgr, "Vestal")
    pierce = get_skill(sb, "Pierce")
    mace = get_skill(vestal, "Mace Bash")

    sb1 = HeroBuild(hero=sb, rank=1, skills=(pierce,))
    members = (
        HeroBuild(hero=vestal, rank=4, skills=(mace,)),
        HeroBuild(hero=vestal, rank=3, skills=(mace,)),
        HeroBuild(hero=vestal, rank=2, skills=(mace,)),
        sb1,
    )
    party = Party(members=members)
    hero_positions = {hero: {4 - i} for i, hero in enumerate(party.members)}

    party._traverse_permutations(hero_positions, party.members, 1)

    assert hero_positions[sb1] == {1}