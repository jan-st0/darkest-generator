from typing import Any
import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
from pathlib import Path 
from enum import Enum

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

def _load_simple_yml_no_fallback(file_path: Path | str) -> dict[str, Any] :
    with open(file_path, "r", encoding="utf-8") as file:
        yml = yaml.load(file, Loader=SafeLoader)

    return yml if isinstance(yml, dict) else {}

def load_hero_data(file_path: str | Path = FilePath.HERO_DATA.value) -> dict[str, Any]:
    """
    Simple wrapper for _load_simple_yml_no_fallback
    """
    return _load_simple_yml_no_fallback(file_path)

def load_trinket_data(file_path: str | Path = FilePath.TRINKET_DATA.value) -> dict[str, Any]:
    """
    Simple wrapper for _load_simple_yml_no_fallback
    """
    return _load_simple_yml_no_fallback(file_path)

def all_hero_variants(hero_data: dict[str, Any]) -> list[str]:
    return list(hero_data['heroes'].keys())


#tests
source = load_hero_data()
print(f'Testing method {all_hero_variants.__name__}')
print(all_hero_variants(source))