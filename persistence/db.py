from typing import Protocol

import pandas as pd

from data_model import (
    ComparisonRequest,
)
from file_manager import FilePaths, append_to_party_comp, read_party_comp
from game_data_manager import GameDataManager

from .domain_mapper import PartyDomainMapper


class PartyDB(Protocol):
    def save_comaparison(self, comp: ComparisonRequest) -> None: ...
    # TODO: Can change all records into a generator
    def load_all_records(self) -> list[ComparisonRequest]: ...
    def to_pandas(self) -> pd.DataFrame: ...


class JsonlDB:
    def __init__(self, gman: GameDataManager):
        self.gman = gman
        self.mapper = PartyDomainMapper(gman)

    def save_comaparison(self, comp: ComparisonRequest) -> None:
        team1 = self.mapper.to_party_domain(comp.party_1)
        team2 = self.mapper.to_party_domain(comp.party_2)
        # if domain check fails, it raises DomainConversionError
        with append_to_party_comp() as f:
            f.write(comp.model_dump_json() + "\n")

    def load_all_records(self) -> list[ComparisonRequest]:
        return [
            ComparisonRequest.model_validate_json(json) for json in read_party_comp()
        ]

    def to_pandas(self) -> pd.DataFrame:
        return pd.read_json(FilePaths.PARTY_COMPARISON_JSONL.value, lines=True)
