import argparse
from typing import Protocol

import uvicorn

from game_data_manager import GameDataManager
from game_utility import GameContext
from persistence import JsonlDB
from party_vectorizer import run_training_pipeline
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


class TrainRankerService:
    def __init__(self, show_plot: bool = False) -> None:
        self.show_plot = show_plot

    def run(self) -> None:
        run_training_pipeline(show_plot=self.show_plot)


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
    parser.add_argument(
        "-r",
        "--train-ranker",
        "--ranker",
        dest="handler",
        action="store_const",
        const=TrainRankerService,
        help="Train the party Ranker model and export it to models/ranker.pkl",
    )
    parser.add_argument(
        "--show-plot",
        action="store_true",
        default=False,
        help="Interactively display the loss plot in addition to exporting to file",
    )
    return parser


if __name__ == "__main__":
    parser = build_args()
    args = parser.parse_args()
    handler = args.handler
    if handler is TrainRankerService:
        handler(show_plot=args.show_plot).run()
    else:
        handler().run()

