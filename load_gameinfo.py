from typing import Any
import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
from pathlib import Path 
from enum import Enum
from functools import cache

type trinkets = dict[str, Any]
type heroes = dict[str, Any]

def find_project_root(marker: str = "pyproject.toml") -> Path:
    """Walk up from this file's directory to locate the repository root."""
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / marker).exists():
            return parent
    return Path.cwd()

ROOT_DIR = find_project_root()

class FilePath(Enum):
    HERO_DATA = ROOT_DIR / 'hero_data.yml'
    TRINKET_DATA = ROOT_DIR / 'trinket_data.yml'

def _load_simple_yml_no_fallback(file_path: Path | str) -> dict[Any, Any] :
    with open(file_path, "r", encoding="utf-8") as file:
        yml = yaml.load(file, Loader=SafeLoader)

    return yml if isinstance(yml, dict) else {}

@cache
def load_hero_data(file_path: str | Path = FilePath.HERO_DATA.value) -> heroes:
    """Simple wrapper for _load_simple_yml_no_fallback."""
    return _load_simple_yml_no_fallback(file_path)

@cache
def load_trinket_data(file_path: str | Path = FilePath.TRINKET_DATA.value) -> trinkets:
    """Simple wrapper for _load_simple_yml_no_fallback."""
    return _load_simple_yml_no_fallback(file_path)

def all_hero_variants(hero_data: heroes) -> list[str]:
    return list(hero_data['heroes'].keys())

def _trinkets_in_category(category: list[dict[str, str]]) -> list[str]:
    return [trinket['name'] for trinket in category]

@cache
def get_generic_trinket_names(file_path: str | Path = FilePath.TRINKET_DATA.value) -> tuple[str, ...]:
    data = load_trinket_data(file_path)
    return tuple(trinket['name'] for trinket in data['trinkets']['generic'])

def valid_trinket_pool_for_hero(hero: str, file_path: str | Path = FilePath.TRINKET_DATA.value) -> list[str]:
    trinket_data = load_trinket_data(file_path)
    return list(get_generic_trinket_names(file_path)) + _trinkets_in_category(trinket_data['trinkets']['hero_specific'][hero])

def all_trinkets_names(file_path: str | Path = FilePath.TRINKET_DATA.value) -> list[str]:
    trinket_data = load_trinket_data(file_path)
    specific = [
        trinket['name']
        for group in trinket_data['trinkets']['hero_specific'].values()
        for trinket in group
    ]
    return  specific + list(get_generic_trinket_names(file_path))


#tests

print(all_trinkets_names())