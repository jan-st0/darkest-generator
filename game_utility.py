from pydantic import BaseModel

from file_manager import load_train_conf
from game_data_manager import GameDataManager
from persistence import PartyDomainMapper, DVectorManager


class ModelConf(BaseModel):
    max_iterations: int = 10
    c_regularization: float = 1.0
    test_split: float


class GameContext:
    def __init__(self) -> None:
        self.gman = GameDataManager()
        self.mapper = PartyDomainMapper(self.gman)
        self.dvec = DVectorManager()
        self.train_conf = load_train_conf()

    def model_conf(self) -> ModelConf:
        return ModelConf.model_validate(self.train_conf)
