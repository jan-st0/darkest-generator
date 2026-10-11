from typing import Annotated
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from data_model import ComparisonRequest
from data_model.exceptions import DomainConversionError
from persistence import PartyDB

router = APIRouter(prefix='/team_comparison', tags=['Team Comparison'])

def get_service(request: Request) -> PartyDB:
    return request.app.state.db_context

@router.post('/create_new', status_code=status.HTTP_201_CREATED)
def create_new_comparison(comparison: ComparisonRequest, db: Annotated[PartyDB, Depends(get_service)]):
    try:
        db.save_comaparison(comparison)
    except DomainConversionError as err:
        # TODO: add error to logs
        print(f'Team comparison invalid: {comparison=}')
        print('Skipping generation')
        raise HTTPException(status_code=400, detail=str(err))
    
@router.get('/health')
async def health():
    return {'status': 'ok'}

def create_team_api(db: PartyDB):
    app = FastAPI()
    app.state.db_context = db
    app.include_router(router)
    return app