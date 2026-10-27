from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from data_model import PartyRequest, PartyScoreResponse
from data_model.exceptions import DomainConversionError
from file_manager import FilePaths
from game_utility import GameContext
from party_vectorizer.fitness import party_to_category_vector
from party_vectorizer.ranker import Ranker

router = APIRouter(prefix="/ranker", tags=["Ranker"])


def get_context(request: Request) -> GameContext:
    return request.app.state.game_ctx


def get_ranker(request: Request) -> Ranker:
    if hasattr(request.app.state, "ranker") and request.app.state.ranker is not None:
        return request.app.state.ranker

    model_path = Path(FilePaths.RANKER_MODEL.value)
    if not model_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ranker model file not found at {model_path}",
        )

    try:
        ranker = Ranker.load(model_path)
        request.app.state.ranker = ranker
        return ranker
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load ranker model: {err}",
        )


@router.post("/score", response_model=PartyScoreResponse)
@router.post("/predict", response_model=PartyScoreResponse)
def score_party(
    party_req: PartyRequest,
    game_ctx: Annotated[GameContext, Depends(get_context)],
    ranker: Annotated[Ranker, Depends(get_ranker)],
):
    try:
        party = game_ctx.mapper.to_party_domain(party_req)
    except DomainConversionError as err:
        raise HTTPException(status_code=400, detail=str(err))

    cat_vector = party_to_category_vector(party, game_ctx)
    score = float(ranker.predict(cat_vector))
    return PartyScoreResponse(score=score)


def create_ranker_api(game_ctx: GameContext, ranker: Ranker | None = None) -> FastAPI:
    if ranker is None:
        model_path = Path(FilePaths.RANKER_MODEL.value)
        if not model_path.exists():
            raise FileNotFoundError(f"Ranker model file not found at {model_path}")
        ranker = Ranker.load(model_path)

    app = FastAPI()
    app.state.game_ctx = game_ctx
    app.state.ranker = ranker
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app
