import math
from typing import Optional
 
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
 
from app.core.deps import CurrentUser, DBDep
from app.models.models import Contact, Corporate, LegalEntity
from app.schemas.schemas import (
    LegalEntityCreate,
    LegalEntityListResponse,
    LegalEntityResponse,
    LegalEntityUpdate,
)
 
router = APIRouter(prefix="/legal-entities", tags=["Razones Sociales"])
 
 
@router.get("", response_model=LegalEntityListResponse)
async def list_legal_entities(
    db: DBDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    corporate_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    is_issuer: Optional[bool] = Query(default=None),
):
    query = select(LegalEntity)
    if search:
        query = query.where(
            LegalEntity.legal_name.ilike(f"%{search}%")
            | LegalEntity.trade_name.ilike(f"%{search}%")
            | LegalEntity.rfc.ilike(f"%{search}%")
        )
    if corporate_id:
        query = query.where(LegalEntity.corporate_id == corporate_id)
    if status:
        query = query.where(LegalEntity.status == status)
    if is_issuer is not None:
        query = query.where(LegalEntity.is_issuer == is_issuer)
 
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(LegalEntity.legal_name)
    )
    entities = result.scalars().all()
 
    items = []
    for entity in entities:
        count_res = await db.execute(
            select(func.count(Contact.id)).where(Contact.legal_entity_id == entity.id)
        )
        resp = LegalEntityResponse.model_validate(entity)
        resp.contacts_count = count_res.scalar_one()
        items.append(resp)
 
    return LegalEntityListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )
 
 
@router.post("", response_model=LegalEntityResponse, status_code=status.HTTP_201_CREATED)
async def create_legal_entity(
    payload: LegalEntityCreate,
    db: DBDep,
    current_user: CurrentUser,
):
    corp = await db.execute(select(Corporate).where(Corporate.id == payload.corporate_id))
    if not corp.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Corporate not found")
    if payload.rfc:
        existing = await db.execute(
            select(LegalEntity).where(LegalEntity.rfc == payload.rfc)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"RFC {payload.rfc} already registered",
            )
    entity = LegalEntity(**payload.model_dump())
    db.add(entity)
    await db.flush()
    await db.refresh(entity)
    return LegalEntityResponse.model_validate(entity)
 
 
@router.get("/{entity_id}", response_model=LegalEntityResponse)
async def get_legal_entity(entity_id: str, db: DBDep, current_user: CurrentUser):
    result = await db.execute(select(LegalEntity).where(LegalEntity.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="Legal entity not found")
    return LegalEntityResponse.model_validate(entity)
 
 
@router.patch("/{entity_id}", response_model=LegalEntityResponse)
async def update_legal_entity(
    entity_id: str,
    payload: LegalEntityUpdate,
    db: DBDep,
    current_user: CurrentUser,
):
    result = await db.execute(select(LegalEntity).where(LegalEntity.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="Legal entity not found")
    if payload.rfc and payload.rfc != entity.rfc:
        existing = await db.execute(
            select(LegalEntity).where(LegalEntity.rfc == payload.rfc)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"RFC {payload.rfc} already registered",
            )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entity, field, value)
    await db.flush()
    await db.refresh(entity)
    return LegalEntityResponse.model_validate(entity)
 
 
@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_legal_entity(
    entity_id: str,
    db: DBDep,
    current_user: CurrentUser,
):
    result = await db.execute(select(LegalEntity).where(LegalEntity.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="Legal entity not found")
    await db.delete(entity)
 