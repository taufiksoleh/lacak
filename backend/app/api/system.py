from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.connectors import CONNECTORS
from app.db import get_db
from app.models import AuditLog
from app.schemas import AuditOut, ConnectorStatus

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/connectors/status")
def connectors_status():
    s = get_settings()
    return {
        "connectors": [
            ConnectorStatus(platform=p, configured=c().is_configured(), limitations=c.limitations)
            for p, c in CONNECTORS.items()
        ],
        "ai": {"configured": s.ai_enabled, "model": s.anthropic_model},
        "timezone": s.timezone,
    }


@router.get("/audit", response_model=list[AuditOut])
def audit_log(
    investigation_id: int | None = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if investigation_id is not None:
        stmt = stmt.where(AuditLog.investigation_id == investigation_id)
    return db.scalars(stmt).all()
