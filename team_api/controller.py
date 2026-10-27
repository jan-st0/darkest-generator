from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from data_model import (
    CombatSkill,
    ComparisonRequest,
    HeroPreviewResponse,
    PartyPreviewResponse,
    PartyRequest,
    Trinket,
)
from data_model.dto.party_stats import HeroSkillStatus
from data_model.exceptions import DomainConversionError
from game_utility import GameContext
from party_vectorizer.fitness import CATEGORY_NAMES, party_to_category_vector
from persistence import PartyDB
from .ranker_controller import router as ranker_router

router = APIRouter(prefix="/team_comparison", tags=["Team Comparison"])


def get_service(request: Request) -> PartyDB:
    return request.app.state.db_context


def get_context(request: Request) -> GameContext:
    return request.app.state.game_ctx


@router.post("/create_new", status_code=status.HTTP_201_CREATED)
def create_new_comparison(
    comparison: ComparisonRequest, db: Annotated[PartyDB, Depends(get_service)]
):
    try:
        db.save_comaparison(comparison)
    except DomainConversionError as err:
        # TODO: add error to logs
        print(f"Team comparison invalid: {comparison=}")
        print("Skipping generation")
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/get_trinket_info/{t_name}", response_model=Trinket)
async def get_trinket_info(
    t_name: str, game_ctx: Annotated[GameContext, Depends(get_context)]
):
    gman = game_ctx.gman
    try:
        return gman.trinkets_by_name[t_name]
    except KeyError as err:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trinket name {t_name}; all valid names: {gman.trinkets_by_name.keys()} \n {err}",
        )


@router.get("/get_skill_info/{s_name}", response_model=CombatSkill)
async def get_skill_info(
    s_name: str, game_ctx: Annotated[GameContext, Depends(get_context)]
):
    gman = game_ctx.gman
    try:
        return gman.skills_by_name[s_name]
    except KeyError as err:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trinket name {s_name}; all valid names: {gman.skills_by_name.keys()} \n {err}",
        )


@router.get("/all_heroes/")
async def get_all_heroes(game_ctx: Annotated[GameContext, Depends(get_context)]):
    return [hero.class_name for hero in game_ctx.gman.heroes]


@router.get("/hero_skills/{h_name}")
async def get_skills_for_hero(
    h_name: str, game_ctx: Annotated[GameContext, Depends(get_context)]
):
    gman = game_ctx.gman
    try:
        hero = gman.heroes_by_name[h_name]
        return [skill.name for skill in hero.combat_skills]
    except KeyError as err:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid hero name {h_name}; all valid names: {gman.heroes_by_name.keys()} \n {err}",
        )


@router.get("/all_neutral_trinkets/")
async def get_neutral_trinkets(game_ctx: Annotated[GameContext, Depends(get_context)]):
    gman = game_ctx.gman
    return [t.name for t in gman.trinkets if t.class_restriction is None]


@router.get("/hero_trinkets/{h_name}")
async def get_hero_specific_trinkets(
    h_name: str, game_ctx: Annotated[GameContext, Depends(get_context)]
):
    gman = game_ctx.gman
    return [t.name for t in gman.trinkets if t.class_restriction == h_name]


@router.get("/game_data_bundle/")
def get_game_data_bundle(game_ctx: Annotated[GameContext, Depends(get_context)]):
    gman = game_ctx.gman
    return {
        "heroes": {
            name: {
                "base_stats": hero.base_stats_lvl6,
                "skills": [s.name for s in hero.combat_skills],
            }
            for name, hero in gman.heroes_by_name.items()
        },
        "skills": {name: skill for name, skill in gman.skills_by_name.items()},
        "trinkets": {name: trinket for name, trinket in gman.trinkets_by_name.items()},
    }


@router.post("/preview_party", response_model=PartyPreviewResponse)
def preview_party(
    party_req: PartyRequest,
    game_ctx: Annotated[GameContext, Depends(get_context)],
):
    try:
        party = game_ctx.mapper.to_party_domain(party_req)
    except DomainConversionError as err:
        raise HTTPException(status_code=400, detail=str(err))

    cat_vector_np = party_to_category_vector(party, game_ctx)
    cat_vector = [round(float(v), 4) for v in cat_vector_np]
    category_scores = dict(zip(CATEGORY_NAMES, cat_vector))

    heroes_preview: list[HeroPreviewResponse] = []
    for member in party.members:
        active_skill_names = {s.name for s in member.active_skills}
        skill_statuses = [
            HeroSkillStatus(
                name=skill.name,
                is_active=skill.name in active_skill_names,
            )
            for skill in member.skills
        ]

        heroes_preview.append(
            HeroPreviewResponse(
                name=member.name,
                rank=member.rank,
                reachable_ranks=sorted(party.hero_pos.get(member, {member.rank})),
                skills=skill_statuses,
                active_skills=[s.name for s in member.active_skills],
                inactive_skills=[
                    s.name for s in member.skills if s.name not in active_skill_names
                ],
                trinkets=[t.name for t in member.trinkets],
            )
        )

    return PartyPreviewResponse(
        has_mark=party.has_mark,
        has_stun=party.has_stun,
        heroes=heroes_preview,
        category_vector=cat_vector,
        category_scores=category_scores,
    )


@router.get("/health")
async def health():
    return {"status": "ok"}


def create_team_api(db: PartyDB, game_ctx: GameContext):
    app = FastAPI()
    app.state.db_context = db
    app.state.game_ctx = game_ctx
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.include_router(ranker_router)
    return app
