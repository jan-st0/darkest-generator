from pydantic import BaseModel


class HeroSkillStatus(BaseModel):
    name: str
    is_active: bool


class HeroPreviewResponse(BaseModel):
    name: str
    rank: int
    reachable_ranks: list[int]
    skills: list[HeroSkillStatus]
    active_skills: list[str]
    inactive_skills: list[str]
    trinkets: list[str]


class PartyPreviewResponse(BaseModel):
    has_mark: bool
    has_stun: bool
    heroes: list[HeroPreviewResponse]
    category_vector: list[float]
    category_scores: dict[str, float]


class PartyScoreResponse(BaseModel):
    score: float
