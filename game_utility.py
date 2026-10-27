from game_data_manager import GameDataManager
from persistence import PartyDomainMapper


class GameContext:
    def __init__(self, gman: GameDataManager) -> None:
        from party_vectorizer.desire_vector import DVectorManager

        self.gman = gman
        self.mapper = PartyDomainMapper(gman)
        self.dvec = DVectorManager()
