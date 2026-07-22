import math
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DBDep
from app.models.models import Corporate, LegalEntity
from app.schemas.schemas import (
    CorporateCreate,
    CorporateListResponse,
    CorporateResponse,
    CorporateUpdate,
)

router = APIRouter(prefix="/corporates", tags=["Corporativos"])


@router.get("", response_model=CorporateListResponse)
async def list_corporates(
    db: DBDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    query = select(Corporate)
    if search:
        query = query.where(
            Corporate.name.ilike(f"%{search}%") | Corporate.trade_name.ilike(f"%{search}%")
        )
    if status:
        query = query.where(Corporate.status == status)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size).order_by(Corporate.name))
    corporates = result.scalars().all()

    items = []
    for corp in corporates:
        count_res = await db.execute(
            select(func.count(LegalEntity.id)).where(LegalEntity.corporate_id == corp.id)
        )
        resp = CorporateResponse.model_validate(corp)
        resp.legal_entities_count = count_res.scalar_one()
        items.append(resp)

    return CorporateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=CorporateResponse, status_code=status.HTTP_201_CREATED)
async def create_corporate(
    payload: CorporateCreate,
    db: DBDep,
    current_user: CurrentUser,
):
    corporate = Corporate(**payload.model_dump())
    db.add(corporate)
    await db.flush()
    await db.refresh(corporate)
    return CorporateResponse.model_validate(corporate)


@router.get("/{corporate_id}", response_model=CorporateResponse)
async def get_corporate(corporate_id: str, db: DBDep, current_user: CurrentUser):
    result = await db.execute(select(Corporate).where(Corporate.id == corporate_id))
    corporate = result.scalar_one_or_none()
    if not corporate:
        raise HTTPException(status_code=404, detail="Corporate not found")
    count_res = await db.execute(
        select(func.count(LegalEntity.id)).where(LegalEntity.corporate_id == corporate.id)
    )
    resp = CorporateResponse.model_validate(corporate)
    resp.legal_entities_count = count_res.scalar_one()
    return resp


@router.patch("/{corporate_id}", response_model=CorporateResponse)
async def update_corporate(
    corporate_id: str,
    payload: CorporateUpdate,
    db: DBDep,
    current_user: CurrentUser,
):
    result = await db.execute(select(Corporate).where(Corporate.id == corporate_id))
    corporate = result.scalar_one_or_none()
    if not corporate:
        raise HTTPException(status_code=404, detail="Corporate not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(corporate, field, value)
    await db.flush()
    await db.refresh(corporate)
    return CorporateResponse.model_validate(corporate)


@router.delete("/{corporate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_corporate(
    corporate_id: str,
    db: DBDep,
    current_user: CurrentUser,
):
    result = await db.execute(select(Corporate).where(Corporate.id == corporate_id))
    corporate = result.scalar_one_or_none()
    if not corporate:
        raise HTTPException(status_code=404, detail="Corporate not found")
    await db.delete(corporate)