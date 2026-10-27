from contextlib import contextmanager
from typing import Any, Generator, TextIO
import yaml
import pickle
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
    GAME_INFO_SOURCE = ROOT_DIR / 'data' / 'darkest_dungeon_data-v4.yml'
    HERO_D_VECTORS = ROOT_DIR / 'data' / 'hero_d_vector.pkl'
    PARTY_COMPARISON_JSONL = ROOT_DIR / 'data' / 'party_comparison.jsonl'
    RANKER_MODEL = ROOT_DIR / 'models' / 'ranker.pkl'
    LOSS_PLOT = ROOT_DIR / 'models' / 'loss_curve.png'

@contextmanager
def append_to_party_comp() -> Generator[TextIO]:
    with open(FilePaths.PARTY_COMPARISON_JSONL.value, encoding='utf-8', mode='a') as file:
        yield file

def read_party_comp() -> Generator[str]:
    with open(FilePaths.PARTY_COMPARISON_JSONL.value, mode='r', encoding='utf-8') as file:
        for line in file:
            yield line.strip()

def _load_simple_yml_no_fallback(file_path: Path | str) -> dict[str, Any] :
    with open(file_path, "r", encoding="utf-8") as file:
        yml: Any = yaml.load(file, Loader=SafeLoader)
    
    return yml if isinstance(yml, dict) else {}

def load_pickle_dict(file_path: Path | str) -> dict[Any, Any]:
    with open(file_path, 'rb') as f:
        table = pickle.load(f)
    return table

def save_model(model: Any, file_path: Path | str = FilePaths.RANKER_MODEL.value) -> Path:
    target_path = Path(file_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, 'wb') as f:
        pickle.dump(model, f)
    return target_path

def load_model(file_path: Path | str = FilePaths.RANKER_MODEL.value) -> Any:
    target_path = Path(file_path)
    with open(target_path, 'rb') as f:
        return pickle.load(f)

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