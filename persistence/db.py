from typing import Protocol
import pandas as pd
from data_model import (
    DomainConversionError,
    ComparisonRequest,
    PartyRequest,
    HeroBuildRequest,
    HeroBuild,
    Party,
)
from file_manager import FilePaths, append_to_party_comp, read_party_comp
from game_data_manager import GameDataManager


class PartyDomainMapper:
    def __init__(self, gman: GameDataManager):
        self.gman = gman

    def to_hero_domain(self, req: HeroBuildRequest, rank: int) -> HeroBuild:
        if req.name not in self.gman.heroes_by_name:
            raise DomainConversionError(f"Unknown hero '{req.name}' at rank {rank}")

        missing_skills = [s for s in req.skills if s not in self.gman.skills_by_name]
        if missing_skills:
            raise DomainConversionError(f"Hero '{req.name}' has unknown skills: {missing_skills}")

        missing_trinkets = [t for t in req.trinkets if t not in self.gman.trinkets_by_name]
        if missing_trinkets:
            raise DomainConversionError(f"Hero '{req.name}' has unknown trinkets: {missing_trinkets}")

        hero = self.gman.heroes_by_name[req.name]
        skill_tuple = tuple(self.gman.skills_by_name[s] for s in req.skills)
        trinket_tuple = tuple(self.gman.trinkets_by_name[t] for t in req.trinkets)

        return HeroBuild(hero, rank, skill_tuple, trinket_tuple)

    def to_party_domain(self, req: PartyRequest) -> Party:
        members = tuple(
            self.to_hero_domain(hero_build, 4 - idx)
            for idx, hero_build in enumerate(req.members)
        )
        return Party(members, self.gman)


class PartyDB(Protocol):
    def save_comaparison(self, comp: ComparisonRequest) -> None: ...
    # TODO: Can change all records into a generator
    def load_all_records(self) -> list[ComparisonRequest]: ...
    def to_pandas(self) -> pd.DataFrame: ...


class JsonlDB:
    def __init__(self, gman: GameDataManager):
        self.gman = gman
        self.mapper = PartyDomainMapper(gman)

    # TODO: Make IO cleaner
    def save_comaparison(self, comp: ComparisonRequest) -> None:
        team1 = self.mapper.to_party_domain(comp.party_1)
        team2 = self.mapper.to_party_domain(comp.party_2)
        # if domain check fails, it raises DomainConversionError
        with append_to_party_comp() as f:
            f.write(comp.model_dump_json() + '\n')

    def load_all_records(self) -> list[ComparisonRequest]:
        return [ComparisonRequest.model_validate_json(json) for json in read_party_comp()]

    def to_pandas(self) -> pd.DataFrame:
        return pd.read_json(FilePaths.PARTY_COMPARISON_JSONL.value, lines=True)