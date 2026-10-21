"""Analisis afiliasi organisasi dengan output terstruktur; klaim tanpa bukti valid dibuang."""

from app.ai.client import UNTRUSTED_NOTE, ask, data_block, response_json

CATEGORIES = ["government", "party", "company", "ngo", "media", "other"]

SCHEMA = {
    "type": "object",
    "properties": {
        "affiliations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "entity_name": {"type": "string"},
                    "category": {"type": "string", "enum": CATEGORIES},
                    "relationship": {"type": "string"},
                    "confidence": {"type": "number"},
                    "rationale": {"type": "string"},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "quote": {"type": "string"},
                            },
                            "required": ["url", "quote"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": [
                    "entity_name",
                    "category",
                    "relationship",
                    "confidence",
                    "rationale",
                    "evidence",
                ],
                "additionalProperties": False,
            },
        },
        "caveats": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["affiliations", "caveats"],
    "additionalProperties": False,
}

SYSTEM = (
    "Anda analis OSINT yang berhati-hati. Dari profil, aktivitas publik, temuan berbasis "
    "aturan, dan hasil riset web, identifikasi indikasi afiliasi akun dengan organisasi, "
    "instansi pemerintah, partai politik, perusahaan, LSM, atau media. Untuk setiap afiliasi: "
    "jelaskan jenis hubungan (mis. pegawai, pejabat, brand ambassador, mitra konten, "
    "pendukung, sekadar berinteraksi), beri confidence 0-1 yang konservatif, dan sertakan "
    "bukti berupa URL yang ADA di data masukan beserta kutipan singkatnya. Jangan membuat URL. "
    "Interaksi publik saja (repost/mention) bukan bukti afiliasi formal; beri confidence "
    "rendah. Tulis rationale dalam Bahasa Indonesia. " + UNTRUSTED_NOTE
)


async def analyze_affiliations(client, context: dict, allowed_urls: set[str]) -> dict:
    response = await ask(
        client,
        system=SYSTEM,
        content="Analisis afiliasi berdasarkan data berikut.\n" + data_block(context),
        schema=SCHEMA,
    )
    data = response_json(response)
    kept = []
    for aff in data.get("affiliations", []):
        evidence = [e for e in aff.get("evidence", []) if e.get("url") in allowed_urls]
        if not evidence:
            continue
        kept.append(
            {
                "entity_name": aff["entity_name"][:200],
                "category": aff["category"],
                "confidence": round(min(1.0, max(0.0, float(aff["confidence"]))), 3),
                "method": "ai",
                "rationale": f"{aff['relationship']}: {aff['rationale']}",
                "evidence": [
                    {"type": "ai", "detail": e.get("quote", "")[:300], "url": e["url"]}
                    for e in evidence
                ],
            }
        )
    return {"affiliations": kept, "caveats": data.get("caveats", [])}
