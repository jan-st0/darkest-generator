import csv
from typing import Iterable

from fastapi import FastAPI
from file_manager import append_party_comparison, party_comparison_exists
from .object_mapper import all_columns

class PartyDB:
    column_names: list[str]
    buffer: list[dict[str, str | int]]

    def create_csv_if_not_exits(self) -> None:
        if not party_comparison_exists():
            with append_party_comparison() as file:
                writer = csv.writer(file)
                writer.writerow(self.column_names)

    def __init__(self) -> None:
        # TODO: check 1 row of csv and adjust column_names
        self.column_names = all_columns()
        self.create_csv_if_not_exits()

    def save_rows(self, rows: list[dict[str, str | int]]) -> None:
        with append_party_comparison() as file:
            writer = csv.DictWriter(file, fieldnames=self.column_names, delimiter='|')
            writer.writerows(rows)
    
    def save_row(self, row: dict[str, str | int]) -> None:
        with append_party_comparison() as file:
            writer = csv.DictWriter(file, fieldnames=self.column_names, delimiter='|')
            writer.writerow(row)

    def buffer_add(self, row: dict[str, str | int]) -> None:
        self.buffer.append(row)
    
    def buffer_mass_add(self, rows: Iterable[dict[str, str | int]]) -> None:
        self.buffer.extend(rows)
    
    def write_buffer(self) -> None:
        self.save_rows(self.buffer)
        self.buffer.clear()


app = FastAPI(
    title='PartyAPI',
    version='0.1.0'
)

def store_