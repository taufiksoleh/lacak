from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors import CONNECTORS
from app.models import Account, Activity, AffiliationFinding, Investigation, WebFinding
from app.schemas import AccountOut, ActivityOut, FindingOut, InvestigationSummary, WebFindingOut
from app.services.collector import build_graph


def account_out(db: Session, acc: Account) -> AccountOut:
    out = AccountOut.model_validate(acc)
    out.activity_count = db.query(Activity).filter(Activity.account_id == acc.id).count()
    return out


def build_report(db: Session, inv: Investigation) -> dict:
    analysis = inv.analysis or {}
    findings = db.scalars(
        select(AffiliationFinding)
        .where(AffiliationFinding.investigation_id == inv.id)
        .order_by(AffiliationFinding.confidence.desc())
    )
    web = db.scalars(select(WebFinding).where(WebFinding.investigation_id == inv.id))
    recent = db.scalars(
        select(Activity)
        .join(Account)
        .where(Account.investigation_id == inv.id)
        .order_by(Activity.created_at.desc())
        .limit(25)
    )
    graph = build_graph(db, inv)
    platforms = sorted({a.platform for a in inv.accounts})
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "investigation": InvestigationSummary.model_validate(inv).model_dump(mode="json"),
        "accounts": [account_out(db, a).model_dump(mode="json") for a in inv.accounts],
        "stats": analysis.get("stats", {}),
        "signals": analysis.get("signals", {}),
        "top_interactions": graph["top"],
        "graph": graph,
        "findings": [FindingOut.model_validate(f).model_dump() for f in findings],
        "web_findings": [WebFindingOut.model_validate(w).model_dump() for w in web],
        "ai": analysis.get("ai"),
        "ai_research": analysis.get("ai_research"),
        "ai_caveats": analysis.get("ai_caveats", []),
        "ai_error": analysis.get("ai_error", ""),
        "recent_activities": [
            ActivityOut.model_validate(a)
            .model_copy(update={"handle": a.account.handle})
            .model_dump(mode="json")
            for a in recent
        ],
        "limitations": [
            {"platform": p, "text": CONNECTORS[p].limitations} for p in platforms if p in CONNECTORS
        ],
    }
