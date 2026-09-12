from typing import Any
import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader # type: ignore[assignment]
from pathlib import Path 
from enum import Enum

def find_project_root(marker: str = "pyproject.toml") -> Path:
    """Walk up from this file's directory to locate the repository root"""
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / marker).exists():
            return parent
    return Path.cwd()

ROOT_DIR = find_project_root()

class FilePaths(Enum):
    GAME_INFO_SOURCE = ROOT_DIR / 'darkest_dungeon_data-v4.yml'


def _load_simple_yml_no_fallback(file_path: Path | str) -> dict[str, Any] :
    with open(file_path, "r", encoding="utf-8") as file:
        yml: Any = yaml.load(file, Loader=SafeLoader)
    
    return yml if isinstance(yml, dict) else {}

type raw_data_type = dict[str, Any]

class GameDataHandler:

    def __init__(self, file_path: Path = FilePaths.GAME_INFO_SOURCE.value) -> None:
        try:
            self._file_path = file_path
            self._raw_data = _load_simple_yml_no_fallback(file_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found: {file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in {file_path}: {e}")

    @property
    def raw_data(self) -> raw_data_type:
        return self._raw_data
    
    @property
    def file_path(self) -> Path:
        return self._file_path