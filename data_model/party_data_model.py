from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING
from data_model.hero_data_model import CombatSkill, HeroBuild

if TYPE_CHECKING:
    from game_data_manager import GameDataManager

type Permutation = tuple[HeroBuild, ...]

# TODO: Change it so that it inherits from collections.abc.Sequence, so permutaion -> slices
# or add getitem
@dataclass(slots=True)
class Party:
    # ranks: 4 3 2 1
    # tuple indices: 0 1 2 3
    members: tuple[HeroBuild, ...]
    mark: bool = field(init=False)
    hero_pos: dict[HeroBuild, set[int]] = field(init=False, default_factory=dict)
    skill_parent_tuple: tuple[tuple[CombatSkill, HeroBuild], ...] = field(init=False)
    all_active_skills: tuple[CombatSkill, ...] = field(init=False)
    man: InitVar[GameDataManager]
    # cached atributes
    has_mark: bool = field(init=False, default=False)
    has_stun: bool = field(init=False, default=False)

    def _flatten_skill_parent(self) -> tuple[tuple[CombatSkill, HeroBuild], ...] :
        return tuple(
            (skill, hero)
            for hero in self.members
            for skill in hero.active_skills
        )
    
    def _flatten_skill(self) -> tuple[CombatSkill, ...]:
        return tuple(
            skill
            for hero in self.members
            for skill in hero.active_skills
        )
    
    def applies_mark(self, man: GameDataManager) -> bool:
        return not man.mark_skills.isdisjoint(self.all_active_skills)
    
    def applies_stun(self, man: GameDataManager) -> bool:
        return not man.stun_skills.isdisjoint(self.all_active_skills)

    def _traverse_permutations(self, positions: dict[HeroBuild, set[int]], perm: Permutation, depth: int) -> None:
        if (depth == 3):
            return None

        def norm_move(begin: int, val: int) -> int:
            """Returns position(4,..,1) after move"""
            return max(1, min(4, begin - val)) 

        def swap(source: tuple, i: int, j: int) -> tuple:
            if i > j:
                i, j = j, i
            return source[:i] + (source[j],) + source[i+1: j] + (source[i],) + source[j+1:]

        for i, hero in enumerate(perm):
            h_pos = 4 - i
            if hero.move_skills is None:
                continue

            for skill in hero.move_skills:
                if h_pos not in skill.launch_ranks:
                    continue

                after_mov = norm_move(h_pos, skill.move_val)
                if after_mov == h_pos:
                    continue
                tuple_after_mov = 4 - after_mov
                hero_swap = perm[tuple_after_mov]
                next_perm = swap(perm, tuple_after_mov, i)
                positions[hero].add(after_mov)
                positions[hero_swap].add(h_pos)
                self._traverse_permutations(positions, next_perm, depth + 1)
                
    def set_active_skills(self) -> None:
        self.hero_pos: dict[HeroBuild, set[int]] = {
            hero: {4 - i}
            for i, hero in enumerate(self.members)
        }
        perm_start = self.members
        self._traverse_permutations(self.hero_pos, perm_start, 1)
        for hero, pos in self.hero_pos.items():
            hero.init_active_skills(pos)
    
    def __post_init__(self, man: GameDataManager) -> None:
        self.set_active_skills()
        self.skill_parent_tuple = self._flatten_skill_parent()
        self.all_active_skills = self._flatten_skill()
        self.has_mark = self.applies_mark(man)
        self.has_stun = self.applies_stun(man)
        for hero in self.members:
            hero.setup_post_active_skills()