from typing import Annotated, Literal

from pydantic import BaseModel, Field


class HeroBuildRequest(BaseModel):
    name: str
    skills: Annotated[list[str], Field(min_length=4, max_length=4)]
    trinkets: Annotated[list[str], Field(max_length=2, default_factory=list)]


class PartyRequest(BaseModel):
    members: Annotated[list[HeroBuildRequest], Field(min_length=4, max_length=4)]


class ComparisonRequest(BaseModel):
    party_1: PartyRequest
    party_2: PartyRequest
    better: Literal[-1, 1, 2] = -1
