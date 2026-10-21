import logging
from collections.abc import Callable
from datetime import UTC, datetime

import anthropic
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai import affiliation, research, summarize
from app.ai.client import AIError, get_client
from app.analysis.activity import activity_stats
from app.analysis.entities import AccountData, ActivityData, EntityDef, load_seed, match_entities
from app.analysis.graph import interaction_graph
from app.analysis.signals import behavior_signals
from app.config import get_settings
from app.connectors import Connector, ConnectorError, get_connector
from app.connectors.base import NormalizedActivity
from app.db import SessionLocal
from app.models import Account, Activity, AffiliationFinding, Entity, Investigation, WebFinding
from app.services import audit

log = logging.getLogger(__name__)

ConnectorFactory = Callable[[str, bool], Connector]


def seed_entities(db: Session) -> None:
    if db.scalar(select(Entity.id).limit(1)) is not None:
        return
    for e in load_seed():
        db.add(Entity(**e))
    db.commit()


def activity_row(account: Account, a: NormalizedActivity, source: str) -> Activity:
    return Activity(
        account=account,
        platform=a.platform,
        type=a.type,
        external_id=a.external_id,
        text=a.text,
        url=a.url,
        created_at=a.created_at,
        targets=a.targets,
        links=a.links,
        metrics=a.metrics,
        source=source,
    )


async def collect(
    investigation_id: int,
    connector_factory: ConnectorFactory = get_connector,
    ai_client=None,
    use_ai: bool = True,
) -> None:
    db = SessionLocal()
    try:
        inv = db.get(Investigation, investigation_id)
        if inv is None:
            return
        inv.status, inv.status_detail = "running", "Mengambil data dari platform…"
        db.commit()
        limit = get_settings().activity_limit
        source = "demo" if inv.demo else "api"
        problems: list[str] = []
        for acc in inv.accounts:
            connector = connector_factory(acc.platform, inv.demo)
            if not connector.is_configured():
                acc.error = f"Konektor {acc.platform} belum dikonfigurasi (isi kredensial di .env)."
                problems.append(acc.error)
                continue
            try:
                profile = await connector.fetch_profile(acc.handle)
                acts = await connector.fetch_activity(profile, limit)
            except ConnectorError as e:
                acc.error = str(e)
                problems.append(acc.error)
                continue
            acc.error = ""
            acc.handle = profile.handle
            acc.external_id = profile.external_id
            acc.display_name = profile.display_name
            acc.bio = profile.bio
            acc.profile_url = profile.profile_url
            acc.links = profile.links
            acc.followers = profile.followers
            acc.following = profile.following
            acc.verified = profile.verified
            acc.created_at_platform = profile.created_at
            acc.raw = profile.raw
            db.execute(
                delete(Activity).where(
                    Activity.account_id == acc.id, Activity.source.in_(["api", "demo"])
                )
            )
            for a in acts:
                db.add(activity_row(acc, a, source))
        db.commit()

        inv.status_detail = "Menganalisis…"
        db.commit()
        client = ai_client if ai_client is not None else (get_client() if use_ai else None)
        await analyze(db, inv, client)
        inv.status = "done"
        inv.status_detail = " ".join(problems)
        inv.collected_at = datetime.now(UTC)
        db.commit()
        audit.log(db, "collect", inv.id, f"selesai; {len(problems)} masalah konektor")
    except Exception as e:  # noqa: BLE001 - status harus selalu diperbarui
        log.exception("collect gagal")
        db.rollback()
        inv = db.get(Investigation, investigation_id)
        if inv is not None:
            inv.status, inv.status_detail = "error", f"Gagal: {e}"
            db.commit()
    finally:
        db.close()


def _load(db: Session, inv: Investigation):
    accounts = list(inv.accounts)
    activities = list(
        db.scalars(
            select(Activity)
            .join(Account)
            .where(Account.investigation_id == inv.id)
            .order_by(Activity.created_at.desc())
        )
    )
    return accounts, activities


async def analyze(db: Session, inv: Investigation, ai_client=None) -> None:
    """Hitung ulang analisis aturan; jalankan AI bila client tersedia (jika tidak, hasil AI
    sebelumnya dipertahankan)."""
    settings = get_settings()
    accounts, activities = _load(db, inv)
    entities = [
        EntityDef(e.name, e.category, e.handles, e.domains, e.keywords)
        for e in db.scalars(select(Entity))
    ]
    stats = activity_stats(
        [(a.platform, a.type, a.created_at) for a in activities], settings.timezone
    )
    signals = behavior_signals(
        [(a.type, a.text, a.created_at) for a in activities],
        [acc.created_at_platform for acc in accounts if acc.created_at_platform],
        settings.timezone,
    )
    rule_findings = match_entities(
        entities,
        [AccountData(a.platform, a.handle, a.bio, a.links, a.profile_url) for a in accounts],
        [ActivityData(a.platform, a.type, a.text, a.url, a.targets, a.links) for a in activities],
    )
    db.execute(
        delete(AffiliationFinding).where(
            AffiliationFinding.investigation_id == inv.id, AffiliationFinding.method == "rule"
        )
    )
    for f in rule_findings:
        db.add(AffiliationFinding(investigation_id=inv.id, **f))

    graph = build_graph(db, inv, accounts, activities)
    previous = inv.analysis or {}
    analysis = {
        "stats": stats,
        "signals": signals,
        "top_interactions": graph["top"],
        "ai": previous.get("ai"),
        "ai_research": previous.get("ai_research"),
        "ai_caveats": previous.get("ai_caveats", []),
        "ai_error": previous.get("ai_error", ""),
        "ai_enabled": settings.ai_enabled,
    }
    if ai_client is not None:
        try:
            await _run_ai(
                db,
                inv,
                ai_client,
                accounts,
                activities,
                stats,
                signals,
                rule_findings,
                graph["top"],
                analysis,
            )
            analysis["ai_error"] = ""
        except (AIError, anthropic.APIError) as e:
            log.warning("AI gagal: %s", e)
            analysis["ai_error"] = f"Analisis AI gagal: {e}"
    inv.analysis = analysis
    db.commit()


async def _run_ai(
    db, inv, client, accounts, activities, stats, signals, rule_findings, top, analysis
) -> None:
    account_ctx = [
        {
            "platform": a.platform,
            "handle": a.handle,
            "nama": a.display_name,
            "bio": a.bio,
            "url_profil": a.profile_url,
            "tautan": a.links,
            "pengikut": a.followers,
        }
        for a in accounts
        if not a.error
    ]
    web = await research.research(client, inv.subject_name, account_ctx)
    db.execute(delete(WebFinding).where(WebFinding.investigation_id == inv.id))
    for s in web["sources"]:
        db.add(WebFinding(investigation_id=inv.id, **s))
    analysis["ai_research"] = web["summary"]

    sample = [
        {
            "platform": a.platform,
            "jenis": a.type,
            "waktu": a.created_at.isoformat(),
            "teks": a.text[:280],
            "url": a.url,
            "target": [t["handle"] for t in a.targets],
        }
        for a in activities[:150]
    ]
    allowed = (
        {a.url for a in activities if a.url}
        | {a.profile_url for a in accounts if a.profile_url}
        | {link for a in accounts for link in a.links}
        | {s["url"] for s in web["sources"]}
    )
    context = {
        "tujuan_investigasi": inv.purpose,
        "akun": account_ctx,
        "aktivitas_terbaru": sample,
        "akun_paling_sering_berinteraksi": top[:15],
        "temuan_aturan": [
            {k: f[k] for k in ("entity_name", "category", "confidence", "rationale")}
            for f in rule_findings
        ],
        "riset_web": {"ringkasan": web["summary"], "sumber": web["sources"]},
    }
    aff = await affiliation.analyze_affiliations(client, context, allowed)
    db.execute(
        delete(AffiliationFinding).where(
            AffiliationFinding.investigation_id == inv.id, AffiliationFinding.method == "ai"
        )
    )
    for f in aff["affiliations"]:
        db.add(AffiliationFinding(investigation_id=inv.id, **f))
    analysis["ai_caveats"] = aff["caveats"]

    context["statistik"] = {k: v for k, v in stats.items() if k not in ("heatmap", "daily")}
    context["indikator_perilaku"] = signals
    context["afiliasi_ai"] = aff["affiliations"]
    analysis["ai"] = await summarize.summarize(client, context, allowed)


def build_graph(db: Session, inv: Investigation, accounts=None, activities=None) -> dict:
    if accounts is None:
        accounts, activities = _load(db, inv)
    entity_handles = {h.lower(): e.name for e in db.scalars(select(Entity)) for h in e.handles}
    return interaction_graph(
        [(a.platform, a.handle) for a in accounts],
        [
            (a.platform, a.account.handle, t["handle"], t.get("kind", "mention"))
            for a in activities
            for t in a.targets
        ],
        entity_handles,
    )
