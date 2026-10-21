"""Riset web publik tentang akun target menggunakan tool web search Claude."""

from app.ai.client import UNTRUSTED_NOTE, ask, data_block, response_text
from app.config import get_settings

SYSTEM = (
    "Anda analis OSINT yang etis untuk keperluan keamanan internet. Cari HANYA informasi "
    "publik tentang akun media sosial yang diberikan: profil resmi, pemberitaan media, "
    "pernyataan di situs organisasi, dan keterkaitan publik dengan organisasi, instansi "
    "pemerintah, partai, atau perusahaan. Jangan mencari atau melaporkan data pribadi sensitif "
    "(alamat rumah, nomor telepon, data keluarga, kesehatan, agama) atau informasi tentang "
    "orang lain yang tidak relevan. Bedakan fakta yang bersumber dari dugaan. Jika tidak ada "
    "informasi yang dapat diverifikasi, katakan demikian. Tulis ringkasan dalam Bahasa "
    "Indonesia dan sebutkan sumber untuk setiap klaim. " + UNTRUSTED_NOTE
)


def _sources(response) -> list[dict]:
    cited: dict[str, dict] = {}
    found: dict[str, dict] = {}
    for block in response.content:
        btype = getattr(block, "type", "")
        if btype == "text":
            for c in getattr(block, "citations", None) or []:
                url = getattr(c, "url", None)
                if url and url not in cited:
                    cited[url] = {
                        "url": url,
                        "title": getattr(c, "title", "") or "",
                        "snippet": getattr(c, "cited_text", "") or "",
                    }
        elif btype == "web_search_tool_result":
            results = getattr(block, "content", None)
            if not isinstance(results, list):  # objek error, bukan daftar hasil
                continue
            for r in results:
                url = getattr(r, "url", None)
                if url and url not in found:
                    found[url] = {"url": url, "title": getattr(r, "title", "") or "", "snippet": ""}
    merged = list(cited.values()) + [v for k, v in found.items() if k not in cited]
    return merged[:20]


async def research(client, subject_name: str, accounts: list[dict]) -> dict:
    content = (
        "Lakukan riset web publik tentang pemilik akun berikut dan keterkaitannya dengan "
        "organisasi/pemerintah/perusahaan.\n"
        + data_block({"nama_subjek": subject_name or None, "akun": accounts})
    )
    response = await ask(
        client,
        system=SYSTEM,
        content=content,
        tools=[
            {
                "type": "web_search_20260209",
                "name": "web_search",
                "max_uses": get_settings().ai_web_search_max_uses,
            }
        ],
    )
    return {"summary": response_text(response).strip(), "sources": _sources(response)}
