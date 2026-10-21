from sqlalchemy.orm import Session

from app.models import AuditLog


def log(db: Session, action: str, investigation_id: int | None = None, detail: str = "") -> None:
    db.add(AuditLog(action=action, investigation_id=investigation_id, detail=detail))
    db.commit()
