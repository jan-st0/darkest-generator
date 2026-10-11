from data_model.party_data_model import Party
from data_model.hero_data_model import HeroBuild
from file_manager import FilePaths
from file_manager import read_party_comp
from file_manager import append_to_party_comp
import pandas as pd
from typing import Protocol
from game_data_manager import GameDataManager
from dataclasses import Field
from typing import Annotated
from pydantic import BaseModel

class DomainConversionError(Exception):
    """Raised when request data cannot be mapped to game domain models."""
    pass

class HeroBuildRequest(BaseModel):
    name: str
    skills: Annotated[list[str], Field(min_length=4, max_length=4)]
    trinkets: Annotated[list[str], Field(max_length=2, default_factory=list)]
    def to_domain(self, rank: int, gman: GameDataManager) -> HeroBuild:
        if self.name not in gman.heroes_by_name:
            raise DomainConversionError(f"Unknown hero '{self.name}' at rank {rank}")

        missing_skills = [s for s in self.skills if s not in gman.skills_by_name]
        if missing_skills:
            raise DomainConversionError(f"Hero '{self.name}' has unknown skills: {missing_skills}")

        missing_trinkets = [t for t in self.trinkets if t not in gman.trinkets_by_name]
        if missing_trinkets:
            raise DomainConversionError(f"Hero '{self.name}' has unknown trinkets: {missing_trinkets}")

        hero = gman.heroes_by_name[self.name]
        skill_tuple = tuple(gman.skills_by_name[s] for s in self.skills)
        trinket_tuple = tuple(gman.trinkets_by_name[t] for t in self.trinkets)

        return HeroBuild(hero, rank, skill_tuple, trinket_tuple)


class PartyRequest(BaseModel):
    members: Annotated[list[HeroBuildRequest], Field(min_length=4, max_length=4)]
    def to_domain(self, gman: GameDataManager) -> Party:
        members = tuple(
            hero_build.to_domain(4 - idx, gman)
            for idx, hero_build in enumerate(self.members)
        )
        return Party(members, gman)

class ComparisonRequest(BaseModel):
    party_1: PartyRequest
    party_2: PartyRequest
    better: int = -1


class PartyDB(Protocol):
    def save_comaprison(self, comp: ComparisonRequest) -> None: ...
    def load_all_records(self) -> list[ComparisonRequest]: ...
    def to_pandas(self) -> pd.DataFrame: ...

class JsonlDB:
    def __init__(self, gman: GameDataManager):
        self.gman = gman

    # TODO: Make IO cleaner
    def save_comaprison(self, comp: ComparisonRequest) -> None:
        with append_to_party_comp() as f:
            f.write(comp.model_dump_json() + '\n')

    def load_all_records(self) -> list[ComparisonRequest]:
        return [ComparisonRequest.model_validate_json(json) for json in read_party_comp()]
            
    def to_pandas(self) -> pd.DataFrame:
        return pd.read_json(FilePaths.PARTY_COMPARISON_JSONL.value, lines=True)
    