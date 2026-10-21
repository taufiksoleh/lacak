from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.connectors.importer import parse_file
from app.db import get_db
from app.models import Account, Activity, AffiliationFinding, Investigation, WebFinding
from app.schemas import (
    ActivityOut,
    FindingOut,
    ImportResult,
    InvestigationCreate,
    InvestigationOut,
    InvestigationSummary,
    TimelinePage,
    WebFindingOut,
)
from app.services import audit, collector
from app.services.report_builder import account_out, build_report

router = APIRouter(prefix="/api/investigations", tags=["investigations"])

MAX_IMPORT_BYTES = 10 * 1024 * 1024


def _get(db: Session, inv_id: int) -> Investigation:
    inv = db.get(Investigation, inv_id)
    if inv is None:
        raise HTTPException(404, "Investigasi tidak ditemukan")
    return inv


def _out(db: Session, inv: Investigation) -> InvestigationOut:
    return InvestigationOut(
        **InvestigationSummary.model_validate(inv).model_dump(),
        accounts=[account_out(db, a) for a in inv.accounts],
        analysis=inv.analysis or {},
    )


@router.get("", response_model=list[InvestigationSummary])
def list_investigations(db: Session = Depends(get_db)):
    return db.scalars(select(Investigation).order_by(Investigation.created_at.desc())).all()


@router.post("", response_model=InvestigationOut, status_code=201)
def create_investigation(body: InvestigationCreate, db: Session = Depends(get_db)):
    inv = Investigation(
        title=body.title, subject_name=body.subject_name, purpose=body.purpose, demo=body.demo
    )
    seen = set()
    for a in body.accounts:
        key = (a.platform, a.handle.lower())
        if key not in seen:
            seen.add(key)
            inv.accounts.append(Account(platform=a.platform, handle=a.handle))
    db.add(inv)
    db.commit()
    audit.log(db, "create", inv.id, f"{inv.title} | tujuan: {inv.purpose[:200]}")
    return _out(db, inv)


@router.get("/{inv_id}", response_model=InvestigationOut)
def get_investigation(inv_id: int, db: Session = Depends(get_db)):
    return _out(db, _get(db, inv_id))


@router.delete("/{inv_id}", status_code=204)
def delete_investigation(inv_id: int, db: Session = Depends(get_db)):
    inv = _get(db, inv_id)
    title = inv.title
    db.delete(inv)
    db.commit()
    audit.log(db, "delete", inv_id, f"seluruh data investigasi '{title}' dihapus")


@router.post("/{inv_id}/collect", response_model=InvestigationSummary, status_code=202)
def start_collect(
    inv_id: int,
    background: BackgroundTasks,
    use_ai: bool = True,
    db: Session = Depends(get_db),
):
    inv = _get(db, inv_id)
    if inv.status == "running":
        raise HTTPException(409, "Pengumpulan data sedang berjalan")
    inv.status, inv.status_detail = "running", "Dalam antrean…"
    db.commit()
    audit.log(db, "collect_start", inv.id, f"use_ai={use_ai}")
    background.add_task(collector.collect, inv.id, use_ai=use_ai)
    return inv


@router.post("/{inv_id}/import", response_model=ImportResult)
async def import_activities(inv_id: int, file: UploadFile, db: Session = Depends(get_db)):
    inv = _get(db, inv_id)
    content = await file.read(MAX_IMPORT_BYTES + 1)
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(413, "File terlalu besar (maks. 10 MB)")
    try:
        rows, errors = parse_file(file.filename or "", content)
    except (ValueError, UnicodeDecodeError) as e:
        raise HTTPException(400, f"File tidak dapat dibaca: {e}") from e
    accounts = {(a.platform, a.handle.lower()): a for a in inv.accounts}
    skipped = 0
    for row in rows:
        key = (row.activity.platform, row.handle)
        if row.activity.platform not in ("instagram", "threads", "x", "youtube"):
            skipped += 1
            errors.append(f"platform '{row.activity.platform}' tidak didukung")
            continue
        acc = accounts.get(key)
        if acc is None:
            acc = Account(platform=row.activity.platform, handle=row.handle)
            inv.accounts.append(acc)
            accounts[key] = acc
        db.add(collector.activity_row(acc, row.activity, "import"))
    db.commit()
    imported = len(rows) - skipped
    await collector.analyze(db, inv)
    audit.log(db, "import", inv.id, f"{file.filename}: {imported} aktivitas")
    return ImportResult(imported=imported, skipped=skipped, errors=errors[:50])


@router.get("/{inv_id}/timeline", response_model=TimelinePage)
def timeline(
    inv_id: int,
    platform: str | None = None,
    type: str | None = None,
    q: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    _get(db, inv_id)
    stmt = select(Activity).join(Account).where(Account.investigation_id == inv_id)
    if platform:
        stmt = stmt.where(Activity.platform == platform)
    if type:
        stmt = stmt.where(Activity.type == type)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Activity.text.ilike(like), Activity.url.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(Activity.created_at.desc()).limit(limit).offset(offset))
    items = [
        ActivityOut.model_validate(a).model_copy(update={"handle": a.account.handle}) for a in rows
    ]
    return TimelinePage(total=total or 0, items=items)


@router.get("/{inv_id}/stats")
def stats(inv_id: int, db: Session = Depends(get_db)):
    analysis = _get(db, inv_id).analysis or {}
    return {"stats": analysis.get("stats", {}), "signals": analysis.get("signals", {})}


@router.get("/{inv_id}/graph")
def graph(inv_id: int, db: Session = Depends(get_db)):
    return collector.build_graph(db, _get(db, inv_id))


@router.get("/{inv_id}/affiliations", response_model=list[FindingOut])
def affiliations(inv_id: int, db: Session = Depends(get_db)):
    _get(db, inv_id)
    return db.scalars(
        select(AffiliationFinding)
        .where(AffiliationFinding.investigation_id == inv_id)
        .order_by(AffiliationFinding.confidence.desc())
    ).all()


@router.get("/{inv_id}/web-findings", response_model=list[WebFindingOut])
def web_findings(inv_id: int, db: Session = Depends(get_db)):
    _get(db, inv_id)
    return db.scalars(select(WebFinding).where(WebFinding.investigation_id == inv_id)).all()


@router.get("/{inv_id}/report")
def report(inv_id: int, db: Session = Depends(get_db)):
    inv = _get(db, inv_id)
    audit.log(db, "report_view", inv.id)
    return build_report(db, inv)
