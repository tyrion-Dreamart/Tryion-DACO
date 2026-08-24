import math
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func

from app.core.deps import CurrentUser, DBDep
from app.models.models import Contact, LegalEntity
from app.schemas.schemas import (
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)

router = APIRouter(prefix="/contacts", tags=["Contactos"])


@router.get("", response_model=ContactListResponse)
async def list_contacts(
    db: DBDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    legal_entity_id: Optional[str] = Query(default=None),
    contact_type: Optional[str] = Query(default=None),
    is_primary: Optional[bool] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
):
    query = select(Contact)
    if search:
        query = query.where(
            Contact.first_name.ilike(f"%{search}%")
            | Contact.last_name.ilike(f"%{search}%")
            | Contact.email.ilike(f"%{search}%")
        )
    if legal_entity_id:
        query = query.where(Contact.legal_entity_id == legal_entity_id)
    if contact_type:
        query = query.where(Contact.contact_type == contact_type)
    if is_primary is not None:
        query = query.where(Contact.is_primary == is_primary)
    if is_active is not None:
        query = query.where(Contact.is_active == is_active)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(Contact.first_name, Contact.last_name)
    )
    contacts = result.scalars().all()
    return ContactListResponse(
        items=[ContactResponse.model_validate(c) for c in contacts],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate,
    db: DBDep,
    current_user: CurrentUser,
):
    entity = await db.execute(
        select(LegalEntity).where(LegalEntity.id == payload.legal_entity_id)
    )
    if not entity.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Legal entity not found")
    if payload.is_primary:
        existing_primaries = await db.execute(
            select(Contact).where(
                Contact.legal_entity_id == payload.legal_entity_id,
                Contact.is_primary == True,
            )
        )
        for existing in existing_primaries.scalars().all():
            existing.is_primary = False
    contact = Contact(**payload.model_dump())
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    return ContactResponse.model_validate(contact)


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: str, db: DBDep, current_user: CurrentUser):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactResponse.model_validate(contact)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    db: DBDep,
    current_user: CurrentUser,
):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    await db.flush()
    await db.refresh(contact)
    return ContactResponse.model_validate(contact)