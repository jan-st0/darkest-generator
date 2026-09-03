from dataclasses import dataclass
class Hero:


@dataclass
class Party:
    team: tuple[Hero, ...] = ()


def team_score()