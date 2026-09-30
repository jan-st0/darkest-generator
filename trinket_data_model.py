import re
from dataclasses import dataclass, field
from typing import Optional

from hero_data_model import Hero, HeroBuild
from party_data_model import Party


@dataclass(frozen=True, slots=True)
class TrinketEffect:
    stat: str
    raw: str
    modifier: Optional[int] = None
    unit: Optional[str] = None
    condition: Optional[str] = None

    def is_torch_effect(self) -> bool:
        if not self.condition:
            return False
        c = self.condition.lower()
        return "torch" in c

    def is_position_dependent(self) -> bool:
        combined = f"{self.stat} {self.condition or ''}".lower()
        return bool(re.search(r"\b(?:pos|position)\s*[1-4]\b", combined))

    def is_utility(self) -> bool:
        s = self.stat.lower()
        return any(k in s for k in ("scouting", "trap disarm", "surprised", "surprise chance"))

    def is_food_effect(self) -> bool:
        if "food" in self.stat.lower():
            return True
        if not self.condition:
            return False
        c = self.condition.lower()
        return "starving" in c or "eating" in c


@dataclass(frozen=True, slots=True)
class Trinket:
    name: str
    rarity: str
    category: str
    effects: tuple[TrinketEffect, ...]
    class_restriction: Optional[str] = None

    @property
    def is_crimson_court(self) -> bool:
        return self.rarity == "Crimson Court" or "Crimson Court" in self.category

    @property
    def is_crystalline(self) -> bool:
        return self.rarity == "Crystalline" or "Crystalline" in self.category


@dataclass(frozen=True, slots=True)
class TrinketRef:
    name: str
    effects: tuple[TrinketEffect, ...]


@dataclass(frozen=True, slots=True)
class TrinketSet:
    set_name: str
    class_name: str
    trinket_1: TrinketRef
    trinket_2: TrinketRef
    set_bonus: tuple[TrinketEffect, ...]
    set_bonus_raw: str


@dataclass(slots=True)
class TrinketEvaluationContext:
    hero_rank: int = 1
    has_melee_skills: bool = True
    has_ranged_skills: bool = True
    has_blight_skills: bool = False
    has_bleed_skills: bool = False
    team_has_mark: bool = False
    is_movement_stable: bool = True
    hero_name: str = ''

    @classmethod
    def from_hero(cls, hero: HeroBuild, party: Party) -> TrinketEvaluationContext:
        return TrinketEvaluationContext(
            hero.rank, hero.has_melee_skills(),
            hero.has_ranged_skills(), hero.has_blight_skills(),
            hero.has_bleed_skills(), party.has_mark, len(party.hero_pos[hero]) == 1,
            hero.name
            )

