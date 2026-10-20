import argparse
from typing import Protocol

import uvicorn

from game_data_manager import GameDataManager
from game_utility import GameContext
from persistence import JsonlDB
from team_comparison_data_api import create_team_api


def make_game_ctx() -> GameContext:
    return GameContext(GameDataManager())


class StrategyDispatch(Protocol):
    def run(self) -> None: ...


class PsService:
    def run(self) -> None:
        game_ctx = make_game_ctx()
        app = create_team_api(JsonlDB(game_ctx.gman), game_ctx)
        uvicorn.run(app)


class NoAction:
    def run(self) -> None:
        pass


def build_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.set_defaults(handler=NoAction)
    parser.add_argument(
        "-ps",
        "--party-comparison-service",
        dest="handler",
        action="store_const",
        const=PsService,
    )
    return parser


if __name__ == "__main__":
    parser = build_args()
    args = parser.parse_args()
    args.handler().run()

