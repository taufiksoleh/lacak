from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Entity
from app.schemas import EntityIn, EntityOut
from app.services import audit

router = APIRouter(prefix="/api/entities", tags=["entities"])


def _clean(values: list[str], lower: bool = True) -> list[str]:
    out = []
    for v in values:
        v = v.strip().lstrip("@")
        if v:
            out.append(v.lower() if lower else v)
    return list(dict.fromkeys(out))


@router.get("", response_model=list[EntityOut])
def list_entities(db: Session = Depends(get_db)):
    return db.scalars(select(Entity).order_by(Entity.category, Entity.name)).all()


@router.post("", response_model=EntityOut, status_code=201)
def create_entity(body: EntityIn, db: Session = Depends(get_db)):
    if db.scalar(select(Entity).where(Entity.name == body.name)):
        raise HTTPException(409, "Entitas dengan nama ini sudah ada")
    ent = Entity(
        name=body.name.strip(),
        category=body.category,
        handles=_clean(body.handles),
        domains=_clean(body.domains),
        keywords=_clean(body.keywords, lower=False),
    )
    db.add(ent)
    db.commit()
    audit.log(db, "entity_create", None, ent.name)
    return ent


@router.delete("/{entity_id}", status_code=204)
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    ent = db.get(Entity, entity_id)
    if ent is None:
        raise HTTPException(404, "Entitas tidak ditemukan")
    db.delete(ent)
    db.commit()
    audit.log(db, "entity_delete", None, ent.name)
