"""Klasifikasi topik/sentimen dan narasi ringkasan laporan."""

from app.ai.client import UNTRUSTED_NOTE, ask, data_block, response_json

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "share_percent": {"type": "integer"},
                    "sentiment": {
                        "type": "string",
                        "enum": ["positif", "netral", "negatif", "campuran"],
                    },
                    "example_urls": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["topic", "share_percent", "sentiment", "example_urls"],
                "additionalProperties": False,
            },
        },
        "notable_activities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["url", "reason"],
                "additionalProperties": False,
            },
        },
        "risk_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "topics", "notable_activities", "risk_notes"],
    "additionalProperties": False,
}

SYSTEM = (
    "Anda menyusun laporan OSINT tentang perilaku publik sebuah akun untuk tujuan keamanan "
    "internet. Gunakan Bahasa Indonesia yang netral dan faktual. Kelompokkan aktivitas ke "
    "topik utama beserta sentimennya, tandai aktivitas yang menonjol (mis. penyebaran hoaks, "
    "ujaran kebencian, promosi terselubung, pola terkoordinasi) dengan URL dari data, dan tulis "
    "ringkasan 2-4 paragraf. Jangan berspekulasi tentang data pribadi sensitif. Sebutkan "
    "keterbatasan data. " + UNTRUSTED_NOTE
)


async def summarize(client, context: dict, allowed_urls: set[str]) -> dict:
    response = await ask(
        client,
        system=SYSTEM,
        content="Susun analisis dari data berikut.\n" + data_block(context),
        schema=SCHEMA,
    )
    data = response_json(response)
    for t in data.get("topics", []):
        t["example_urls"] = [u for u in t.get("example_urls", []) if u in allowed_urls][:3]
    data["notable_activities"] = [
        n for n in data.get("notable_activities", []) if n.get("url") in allowed_urls
    ][:15]
    return data
