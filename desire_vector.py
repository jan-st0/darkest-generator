from pathlib import Path
from typing import Any, Optional, Sequence, TYPE_CHECKING
import pickle
import numpy as np
import numpy.typing as npt
from file_manager import FilePaths, load_pickle_dict

if TYPE_CHECKING:
    from game_data_manager import GameDataManager
    from hero_data_model import CombatSkill, Hero
    from trinket_data_model import Trinket, TrinketEvaluationContext

type d_vec_type = dict[str, npt.NDArray[np.float64]]

# Canonical order of buff and debuff stats in vectors
BUFF_STAT_ORDER: tuple[str, ...] = (
    "ACC",
    "BLEED_RESIST",
    "BLIGHT_CHANCE",
    "BLIGHT_RESIST",
    "CRIT",
    "DEBUFF_RESIST",
    "DMG",
    "DODGE",
    "MOVE_RESIST",
    "PROT",
    "SPD",
    "STRESS_RECEIVED",
)

DEBUFF_STAT_ORDER: tuple[str, ...] = (
    "ACC",
    "BLEED_RESIST",
    "BLIGHT_RESIST",
    "CRIT",
    "DMG",
    "DODGE",
    "PROT",
    "SPD",
)

# Strategic weights for enemy debuffs in Darkest Dungeon
DEFAULT_DEBUFF_WEIGHTS: dict[str, float] = {
    "ACC": 0.95,           # Lowers enemy hit rates, protecting party from dmg/crit/stress
    "BLEED_RESIST": 0.45,  # Situational depending on team bleed composition
    "BLIGHT_RESIST": 0.45, # Situational depending on team blight composition
    "CRIT": 0.55,          # Prevents burst damage and party stress spikes
    "DMG": 0.85,           # Directly mitigates incoming damage spikes
    "DODGE": 0.75,         # Ensures party attacks land on evasive backliners
    "PROT": 0.85,          # Shreds damage reduction on tanky enemies
    "SPD": 0.90,           # Allows party to act before enemies, eliminating threats early
}

# Hero desire weights for combat buff stats (1.0 is baseline benefit)
HERO_STAT_DESIRES: dict[str, dict[str, float]] = {
    "Abomination": {
        "ACC": 1.3, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 1.5, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.0, "DEBUFF_RESIST": 0.6, "DMG": 1.6, "DODGE": 0.7,
        "MOVE_RESIST": 0.8, "PROT": 1.0, "SPD": 1.4, "STRESS_RECEIVED": 1.8,
    },
    "Antiquarian": {
        "ACC": 0.4, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 0.8, "BLIGHT_RESIST": 0.6,
        "CRIT": 0.3, "DEBUFF_RESIST": 0.6, "DMG": 0.2, "DODGE": 1.9,
        "MOVE_RESIST": 0.8, "PROT": 0.8, "SPD": 1.5, "STRESS_RECEIVED": 1.2,
    },
    "Arbalest": {
        "ACC": 1.3, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.7, "DEBUFF_RESIST": 0.7, "DMG": 1.8, "DODGE": 0.7,
        "MOVE_RESIST": 1.3, "PROT": 0.8, "SPD": 1.4, "STRESS_RECEIVED": 0.9,
    },
    "Bounty Hunter": {
        "ACC": 1.3, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.4, "DEBUFF_RESIST": 0.7, "DMG": 1.8, "DODGE": 0.8,
        "MOVE_RESIST": 0.9, "PROT": 0.8, "SPD": 1.3, "STRESS_RECEIVED": 0.9,
    },
    "Crusader": {
        "ACC": 1.3, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.0, "DEBUFF_RESIST": 0.7, "DMG": 1.4, "DODGE": 0.3,
        "MOVE_RESIST": 1.1, "PROT": 1.3, "SPD": 1.6, "STRESS_RECEIVED": 0.8,
    },
    "Flagellant": {
        "ACC": 1.2, "BLEED_RESIST": 0.2, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.5,
        "CRIT": 1.1, "DEBUFF_RESIST": 0.6, "DMG": 1.3, "DODGE": 0.3,
        "MOVE_RESIST": 0.8, "PROT": 0.7, "SPD": 1.5, "STRESS_RECEIVED": 0.6,
    },
    "Grave Robber": {
        "ACC": 1.0, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 1.1, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.8, "DEBUFF_RESIST": 0.6, "DMG": 1.7, "DODGE": 1.8,
        "MOVE_RESIST": 0.4, "PROT": 0.3, "SPD": 1.5, "STRESS_RECEIVED": 1.0,
    },
    "Hellion": {
        "ACC": 1.3, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.3, "DEBUFF_RESIST": 0.9, "DMG": 1.8, "DODGE": 0.8,
        "MOVE_RESIST": 1.0, "PROT": 0.7, "SPD": 1.3, "STRESS_RECEIVED": 0.9,
    },
    "Highwayman": {
        "ACC": 1.3, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.7, "DEBUFF_RESIST": 0.6, "DMG": 1.7, "DODGE": 1.4,
        "MOVE_RESIST": 0.5, "PROT": 0.5, "SPD": 1.4, "STRESS_RECEIVED": 0.9,
    },
    "Houndmaster": {
        "ACC": 1.3, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.2, "DEBUFF_RESIST": 0.7, "DMG": 1.4, "DODGE": 1.7,
        "MOVE_RESIST": 0.7, "PROT": 0.7, "SPD": 1.4, "STRESS_RECEIVED": 0.8,
    },
    "Jester": {
        "ACC": 1.0, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.9, "DEBUFF_RESIST": 0.6, "DMG": 1.3, "DODGE": 1.6,
        "MOVE_RESIST": 0.4, "PROT": 0.4, "SPD": 1.6, "STRESS_RECEIVED": 0.6,
    },
    "Leper": {
        "ACC": 2.2, "BLEED_RESIST": 0.7, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.7,
        "CRIT": 1.0, "DEBUFF_RESIST": 0.7, "DMG": 1.6, "DODGE": 0.2,
        "MOVE_RESIST": 1.4, "PROT": 1.0, "SPD": 1.5, "STRESS_RECEIVED": 0.7,
    },
    "Man-at-Arms": {
        "ACC": 1.0, "BLEED_RESIST": 0.7, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.7,
        "CRIT": 0.6, "DEBUFF_RESIST": 0.8, "DMG": 0.7, "DODGE": 1.4,
        "MOVE_RESIST": 1.2, "PROT": 1.9, "SPD": 1.4, "STRESS_RECEIVED": 1.3,
    },
    "Musketeer": {
        "ACC": 1.3, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.7, "DEBUFF_RESIST": 0.7, "DMG": 1.8, "DODGE": 0.7,
        "MOVE_RESIST": 1.3, "PROT": 0.8, "SPD": 1.4, "STRESS_RECEIVED": 0.9,
    },
    "Occultist": {
        "ACC": 1.3, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.3, "DEBUFF_RESIST": 0.7, "DMG": 0.8, "DODGE": 1.2,
        "MOVE_RESIST": 0.9, "PROT": 0.6, "SPD": 1.6, "STRESS_RECEIVED": 1.1,
    },
    "Plague Doctor": {
        "ACC": 1.4, "BLEED_RESIST": 0.7, "BLIGHT_CHANCE": 2.0, "BLIGHT_RESIST": 0.7,
        "CRIT": 0.6, "DEBUFF_RESIST": 0.7, "DMG": 0.3, "DODGE": 1.1,
        "MOVE_RESIST": 1.0, "PROT": 0.5, "SPD": 1.9, "STRESS_RECEIVED": 1.1,
    },
    "Shieldbreaker": {
        "ACC": 1.3, "BLEED_RESIST": 0.6, "BLIGHT_CHANCE": 1.4, "BLIGHT_RESIST": 0.6,
        "CRIT": 1.4, "DEBUFF_RESIST": 0.7, "DMG": 1.7, "DODGE": 1.3,
        "MOVE_RESIST": 0.4, "PROT": 0.5, "SPD": 1.6, "STRESS_RECEIVED": 1.0,
    },
    "Vestal": {
        "ACC": 0.8, "BLEED_RESIST": 0.7, "BLIGHT_CHANCE": 0.0, "BLIGHT_RESIST": 0.7,
        "CRIT": 0.6, "DEBUFF_RESIST": 0.7, "DMG": 0.4, "DODGE": 0.9,
        "MOVE_RESIST": 1.2, "PROT": 0.9, "SPD": 1.5, "STRESS_RECEIVED": 1.1,
    },
}

# Extended hero desires for trinket-exclusive stats
HERO_EXTENDED_DESIRES: dict[str, dict[str, float]] = {
    "Abomination": {"MAX HP": 1.1, "Healing Skills": 0.0, "Stun Skill Chance": 1.5, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
    "Antiquarian": {"MAX HP": 1.0, "Healing Skills": 0.5, "Stun Skill Chance": 0.0, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
    "Arbalest": {"MAX HP": 1.0, "Healing Skills": 1.4, "Stun Skill Chance": 0.0, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
    "Bounty Hunter": {"MAX HP": 1.0, "Healing Skills": 0.0, "Stun Skill Chance": 1.6, "Bleed Skill Chance": 0.5, "Death Blow Resist": 0.6},
    "Crusader": {"MAX HP": 1.2, "Healing Skills": 1.0, "Stun Skill Chance": 1.5, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
    "Flagellant": {"MAX HP": 0.6, "Healing Skills": 1.5, "Stun Skill Chance": 0.0, "Bleed Skill Chance": 1.8, "Death Blow Resist": 1.5},
    "Grave Robber": {"MAX HP": 0.8, "Healing Skills": 0.0, "Stun Skill Chance": 0.0, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
    "Hellion": {"MAX HP": 1.0, "Healing Skills": 0.0, "Stun Skill Chance": 1.4, "Bleed Skill Chance": 1.4, "Death Blow Resist": 0.6},
    "Highwayman": {"MAX HP": 0.9, "Healing Skills": 0.0, "Stun Skill Chance": 0.0, "Bleed Skill Chance": 1.1, "Death Blow Resist": 0.6},
    "Houndmaster": {"MAX HP": 0.9, "Healing Skills": 0.0, "Stun Skill Chance": 1.5, "Bleed Skill Chance": 1.6, "Death Blow Resist": 0.6},
    "Jester": {"MAX HP": 0.8, "Healing Skills": 0.0, "Stun Skill Chance": 0.0, "Bleed Skill Chance": 1.5, "Death Blow Resist": 0.6},
    "Leper": {"MAX HP": 1.2, "Healing Skills": 0.0, "Stun Skill Chance": 0.0, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
    "Man-at-Arms": {"MAX HP": 1.3, "Healing Skills": 0.0, "Stun Skill Chance": 1.6, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
    "Musketeer": {"MAX HP": 1.0, "Healing Skills": 1.4, "Stun Skill Chance": 0.0, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
    "Occultist": {"MAX HP": 1.0, "Healing Skills": 2.0, "Stun Skill Chance": 1.8, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
    "Plague Doctor": {"MAX HP": 0.9, "Healing Skills": 0.7, "Stun Skill Chance": 2.0, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
    "Shieldbreaker": {"MAX HP": 0.9, "Healing Skills": 0.0, "Stun Skill Chance": 0.0, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
    "Vestal": {"MAX HP": 1.2, "Healing Skills": 2.4, "Stun Skill Chance": 1.3, "Bleed Skill Chance": 0.0, "Death Blow Resist": 0.6},
}


def generate_default_debuff_vector(
    game_manager: Optional["GameDataManager"] = None,
) -> npt.NDArray[np.float64]:
    """Generates the standard enemy debuff weight vector matching debuff stat ordering."""
    if game_manager is not None:
        stat_order = game_manager.all_debuff_types
    else:
        stat_order = DEBUFF_STAT_ORDER
    return np.array([DEFAULT_DEBUFF_WEIGHTS.get(stat, 0.5) for stat in stat_order], dtype=np.float64)


def generate_default_desire_vectors(
    game_manager: Optional["GameDataManager"] = None,
) -> d_vec_type:
    """Generates hero desire vectors matching the 12-stat buff vector ordering for each class."""
    if game_manager is not None:
        stat_order = game_manager.all_buff_types
        hero_names = [h.class_name for h in game_manager.heroes]
    else:
        stat_order = BUFF_STAT_ORDER
        hero_names = list(HERO_STAT_DESIRES.keys())

    desire_dict: d_vec_type = {}
    for hero_name in hero_names:
        stat_map = HERO_STAT_DESIRES.get(hero_name, {})
        vec = np.array([stat_map.get(stat, 1.0) for stat in stat_order], dtype=np.float64)
        desire_dict[hero_name] = vec

    return desire_dict


def create_default_vector_data(
    game_manager: Optional["GameDataManager"] = None,
) -> dict[str, Any]:
    """Creates the complete raw data dictionary containing debuff and desire vectors."""
    return {
        "desire_vectors": generate_default_desire_vectors(game_manager),
        "debuff_vector": generate_default_debuff_vector(game_manager),
        "extended_desires": HERO_EXTENDED_DESIRES,
        "buff_stat_order": BUFF_STAT_ORDER,
        "debuff_stat_order": DEBUFF_STAT_ORDER,
    }


def save_default_vectors(
    path: Path | str = FilePaths.HERO_D_VECTORS.value,
    game_manager: Optional["GameDataManager"] = None,
) -> Path:
    """Serializes the default desire and debuff vectors to disk via pickle."""
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    data = create_default_vector_data(game_manager)
    with open(target_path, "wb") as f:
        pickle.dump(data, f)
    return target_path


class DVectorManager:
    _raw_data: dict[str, Any]

    def __init__(self, path: Optional[Path | str] = None) -> None:
        target_path = Path(path) if path is not None else FilePaths.HERO_D_VECTORS.value
        if not target_path.exists():
            save_default_vectors(target_path)
        self._raw_data = load_pickle_dict(target_path)

    @property
    def vec(self) -> d_vec_type:
        """Should be the same as buff vectors"""
        return self._raw_data["desire_vectors"]

    @property
    def debuff(self) -> npt.NDArray[np.float64]:
        return self._raw_data["debuff_vector"]

    @property
    def extended_desires(self) -> dict[str, dict[str, float]]:
        return self._raw_data.get("extended_desires", HERO_EXTENDED_DESIRES)

    def score_buff(
        self,
        skill: CombatSkill,
        caster: Hero,
        party: Optional[Sequence[Hero]] = None,
        game_manager: Optional[GameDataManager] = None,
    ) -> float:
        """Calculates buff score for a skill on the caster or party."""
        return calculate_buff_score(skill, caster, party, self, game_manager)

    def score_debuff(
        self,
        skill: CombatSkill,
        game_manager: Optional[GameDataManager] = None,
        num_targets: Optional[int] = None,
    ) -> float:
        """Calculates debuff score for an enemy debuff skill."""
        return calculate_debuff_score(skill, self, game_manager, num_targets)

    def score_trinket(
        self,
        trinket: "Trinket",
        hero: "Hero",
        context: Optional["TrinketEvaluationContext"] = None,
        game_manager: Optional["GameDataManager"] = None,
    ) -> float:
        """Calculates trinket score for a hero based on desire vector and hero profile."""
        return calculate_trinket_score(trinket, hero, context, self, game_manager)


def calculate_buff_score(
    skill: "CombatSkill",
    caster: "Hero",
    party: Optional[Sequence["Hero"]] = None,
    d_manager: Optional[DVectorManager] = None,
    game_manager: Optional["GameDataManager"] = None,
) -> float:
    """Calculates buff score using the hero desire vector and skill buff vector.

    Heuristic rules (diagram.md):
    - Negative values in buff vector for self/friendly debuffs (e.g. Revenge -10 DODGE).
    - If skill targets 'self': dot product with caster's desire vector.
    - If skill targets 'party': sum dot products across party members.
    - If skill targets 'ally': max dot product across party members (best recipient).
    """
    if not skill.is_buff():
        return 0.0

    if game_manager is None:
        from game_data_manager import GameDataManager
        game_manager = GameDataManager()

    if d_manager is None:
        d_manager = DVectorManager()

    skill_vec = game_manager.skills_buff_values.get(skill)
    if skill_vec is None or not np.any(skill_vec):
        return 0.0

    target_type = getattr(skill, "target_type", "self")

    if target_type == "self" or not party:
        desire = d_manager.vec.get(caster.class_name)
        if desire is None:
            return 0.0
        return float(np.dot(skill_vec, desire))

    if target_type == "party":
        total_score = 0.0
        for h in party:
            desire = d_manager.vec.get(h.class_name)
            if desire is not None:
                total_score += float(np.dot(skill_vec, desire))
        return total_score

    if target_type == "ally":
        scores = []
        for h in party:
            desire = d_manager.vec.get(h.class_name)
            if desire is not None:
                scores.append(float(np.dot(skill_vec, desire)))
        return max(scores, default=0.0)

    # Fallback to caster
    desire = d_manager.vec.get(caster.class_name)
    return float(np.dot(skill_vec, desire)) if desire is not None else 0.0


def calculate_debuff_score(
    skill: "CombatSkill",
    d_manager: Optional[DVectorManager] = None,
    game_manager: Optional["GameDataManager"] = None,
    num_targets: Optional[int] = None,
) -> float:
    """Calculates enemy debuff strength using weighted sum / dot product (diagram.md n88)."""
    if not skill.is_debuff():
        return 0.0

    if game_manager is None:
        from game_data_manager import GameDataManager
        game_manager = GameDataManager()

    if d_manager is None:
        d_manager = DVectorManager()

    skill_vec = game_manager.skills_debuff_values.get(skill)
    if skill_vec is None or not np.any(skill_vec):
        return 0.0

    base_score = float(np.dot(skill_vec, d_manager.debuff))
    targets = num_targets if num_targets is not None else skill.amount_of_targets()
    return base_score * targets


def trinket_to_buff_vector(
    trinket: "Trinket",
    context: Optional["TrinketEvaluationContext"] = None,
    game_manager: Optional["GameDataManager"] = None,
) -> npt.NDArray[np.float64]:
    """Maps the evaluated stats of a trinket into a 12-element normalized buff vector."""
    if game_manager is None:
        from game_data_manager import GameDataManager
        game_manager = GameDataManager()

    from trinket_evaluator import evaluate_trinket_stats
    eff_stats = evaluate_trinket_stats(trinket, context)
    stat_types = game_manager.all_buff_types
    max_map = game_manager.max_values_for_buffs

    vec = np.zeros(len(stat_types), dtype=np.float64)
    stat_indices = {stat: i for i, stat in enumerate(stat_types)}

    # Map core stats from trinket to buff stat index
    acc = eff_stats.get("ACC", 0.0) + eff_stats.get("ACC Melee Skills", 0.0) + eff_stats.get("ACC Ranged Skills", 0.0)
    if "ACC" in stat_indices:
        vec[stat_indices["ACC"]] = acc

    dmg = eff_stats.get("DMG", 0.0) + eff_stats.get("DMG Melee Skills", 0.0) + eff_stats.get("DMG Ranged Skills", 0.0)
    if "DMG" in stat_indices:
        vec[stat_indices["DMG"]] = dmg

    crit = eff_stats.get("CRIT", 0.0) + eff_stats.get("CRIT Melee Skills", 0.0) + eff_stats.get("CRIT Ranged Skills", 0.0)
    if "CRIT" in stat_indices:
        vec[stat_indices["CRIT"]] = crit

    spd = eff_stats.get("SPD", 0.0) + eff_stats.get("SPD after First Round", 0.0)
    if "SPD" in stat_indices:
        vec[stat_indices["SPD"]] = spd

    if "DODGE" in stat_indices:
        vec[stat_indices["DODGE"]] = eff_stats.get("DODGE", 0.0)

    if "PROT" in stat_indices:
        vec[stat_indices["PROT"]] = eff_stats.get("PROT", 0.0)

    bleed_res = eff_stats.get("Bleed Resist", 0.0) + eff_stats.get("Bleed/Blight Resist", 0.0) + eff_stats.get("Debuff/Bleed Resist", 0.0)
    if "BLEED_RESIST" in stat_indices:
        vec[stat_indices["BLEED_RESIST"]] = bleed_res

    blight_res = eff_stats.get("Blight Resist", 0.0) + eff_stats.get("Blight/Bleed Resist", 0.0) + eff_stats.get("Disease/Blight Resist", 0.0) + eff_stats.get("Blight/Disease Resist", 0.0)
    if "BLIGHT_RESIST" in stat_indices:
        vec[stat_indices["BLIGHT_RESIST"]] = blight_res

    debuff_res = eff_stats.get("Debuff Resist", 0.0) + eff_stats.get("Debuff/Bleed Resist", 0.0) + eff_stats.get("Stun/Debuff Resist", 0.0)
    if "DEBUFF_RESIST" in stat_indices:
        vec[stat_indices["DEBUFF_RESIST"]] = debuff_res

    move_res = eff_stats.get("Move Resist", 0.0) + eff_stats.get("Stun/Move Resist", 0.0)
    if "MOVE_RESIST" in stat_indices:
        vec[stat_indices["MOVE_RESIST"]] = move_res

    blight_chance = eff_stats.get("Blight Skill Chance", 0.0) + eff_stats.get("Blight/Debuff Skill Chance", 0.0)
    if "BLIGHT_CHANCE" in stat_indices:
        vec[stat_indices["BLIGHT_CHANCE"]] = blight_chance

    # On trinkets, positive Stress means extra stress taken (+Stress is undesirable).
    # Since max_map["STRESS_RECEIVED"] is -20.0 (stress reduction), positive Stress divided by -20.0
    # produces a negative (penalty) value in the normalized vector.
    stress = eff_stats.get("Stress", 0.0)
    if "STRESS_RECEIVED" in stat_indices:
        vec[stat_indices["STRESS_RECEIVED"]] = stress

    # Normalize by max values
    inv_max = np.array(
        [1.0 / max_map[s] if max_map.get(s, 0.0) != 0 else 0.0 for s in stat_types],
        dtype=np.float64,
    )
    return vec * inv_max


def calculate_trinket_score(
    trinket: "Trinket",
    hero: "Hero",
    context: Optional["TrinketEvaluationContext"] = None,
    d_manager: Optional[DVectorManager] = None,
    game_manager: Optional["GameDataManager"] = None,
) -> float:
    """Calculates overall trinket suitability score for a hero (diagram.md n12 -> n15, n20, n22, n23).

    Evaluates:
    1. Special conditions and ignored item exceptions.
    2. Class restriction match (score 0.0 if not equipable).
    3. Core combat stats against hero's desire vector (dot product).
    4. Utility stats (scouting, trap disarm, surprise) via min-max scaling.
    5. Extended stats (Healing Skills, Stun Chance, Bleed Chance, MAX HP) scaled by hero capabilities.
    """
    from trinket_evaluator import is_trinket_ignored, evaluate_trinket_stats, UTILITY_STATS

    if is_trinket_ignored(trinket.name):
        return 0.0

    if trinket.class_restriction and trinket.class_restriction != hero.class_name:
        return 0.0

    if game_manager is None:
        from game_data_manager import GameDataManager
        game_manager = GameDataManager()

    if d_manager is None:
        d_manager = DVectorManager()

    if context is None:
        from trinket_data_model import TrinketEvaluationContext
        has_melee = any(s.type == "Melee" for s in hero.combat_skills)
        has_ranged = any(s.type == "Ranged" for s in hero.combat_skills)
        has_blight = any(s.blight.chance_lvl5 is not None for s in hero.combat_skills)
        has_bleed = any(s.bleed.chance_lvl5 is not None for s in hero.combat_skills)
        context = TrinketEvaluationContext(
            has_melee_skills=has_melee,
            has_ranged_skills=has_ranged,
            has_blight_skills=has_blight,
            has_bleed_skills=has_bleed,
        )

    eff_stats = evaluate_trinket_stats(trinket, context)
    if not eff_stats:
        return 0.0

    # 1. Core combat stats via desire vector dot product
    trinket_vec = trinket_to_buff_vector(trinket, context, game_manager)
    hero_desire = d_manager.vec.get(hero.class_name)
    core_score = float(np.dot(trinket_vec, hero_desire)) if hero_desire is not None else 0.0

    # 2. Utility stats via min-max scaling (diagram.md n22 -> n23)
    utility_score = 0.0
    scout = eff_stats.get("Scouting Chance", 0.0) + eff_stats.get("Scouting", 0.0)
    if scout != 0.0:
        utility_score += (scout / 25.0) * 0.8

    trap = eff_stats.get("Trap Disarm Chance", 0.0)
    if trap != 0.0:
        utility_score += (trap / 30.0) * 0.7

    surprise_monsters = eff_stats.get("Chance Monsters Surprised", 0.0) + eff_stats.get("Surprise Chance", 0.0)
    if surprise_monsters != 0.0:
        utility_score += (surprise_monsters / 20.0) * 0.8

    surprise_party = eff_stats.get("Chance Party Surprised", 0.0)
    if surprise_party != 0.0:
        utility_score -= (surprise_party / 20.0) * 0.8

    # 3. Extended stats
    ext_desires = d_manager.extended_desires.get(hero.class_name, {})
    ext_score = 0.0

    max_hp = eff_stats.get("MAX HP", 0.0)
    if max_hp != 0.0:
        ext_score += (max_hp / 33.0) * ext_desires.get("MAX HP", 1.0)

    healing_skills = eff_stats.get("Healing Skills", 0.0)
    if healing_skills != 0.0:
        ext_score += (healing_skills / 50.0) * ext_desires.get("Healing Skills", 0.0)

    healing_recv = eff_stats.get("Healing Received", 0.0)
    if healing_recv != 0.0:
        ext_score += (healing_recv / 40.0) * 0.8

    stun_chance = eff_stats.get("Stun Skill Chance", 0.0) + eff_stats.get("Debuff/Stun/Move Skill Chance", 0.0)
    if stun_chance != 0.0:
        ext_score += (stun_chance / 35.0) * ext_desires.get("Stun Skill Chance", 0.0)

    bleed_chance = eff_stats.get("Bleed Skill Chance", 0.0)
    if bleed_chance != 0.0:
        ext_score += (bleed_chance / 40.0) * ext_desires.get("Bleed Skill Chance", 0.0)

    stun_res = eff_stats.get("Stun Resist", 0.0)
    if stun_res != 0.0:
        ext_score += (stun_res / 50.0) * 0.7

    death_blow = eff_stats.get("Death Blow Resist", 0.0)
    if death_blow != 0.0:
        ext_score += (death_blow / 15.0) * ext_desires.get("Death Blow Resist", 0.6)

    virtue = eff_stats.get("Virtue Chance", 0.0)
    if virtue != 0.0:
        ext_score += (virtue / 25.0) * 0.7

    # Restraining Padlock / Abomination stress mitigation
    trans_stress = eff_stats.get("Transformation Stress", 0.0)
    party_stress = eff_stats.get("Stress Inflicted on Party", 0.0)
    if trans_stress < 0:
        ext_score += (-trans_stress / 40.0) * 1.5
    if party_stress < 0:
        ext_score += (-party_stress / 40.0) * 1.5

    return core_score + utility_score + ext_score