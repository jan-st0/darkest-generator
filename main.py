from typing import Protocol
import argparse
class StrategyDispatch(Protocol):
    def run(self) -> None: ...

class PsService:
    def run(self) -> None:
        # TODO: create service
        print('helu')
class NoAction:
    def run(self) -> None:
        pass

def build_args() -> argparse.ArgumentParser :
    parser = argparse.ArgumentParser()
    parser.set_defaults(handler=NoAction)
    parser.add_argument(
        '-ps', '--party-comparison-service',
        dest='handler', action='store_const',
        const=PsService
    )
    return parser

if __name__ == '__main__':
    parser = build_args()
    args = parser.parse_args()
    args.handler().run()

    