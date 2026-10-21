import json
from types import SimpleNamespace as NS


def text(t, citations=None):
    return NS(type="text", text=t, citations=citations)


def msg(*blocks, stop="end_turn"):
    return NS(content=list(blocks), stop_reason=stop)


class FakeMessages:
    def __init__(self, handler):
        self.handler = handler
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.handler(kwargs, len(self.calls))


class FakeClient:
    def __init__(self, handler):
        self.beta = NS(messages=FakeMessages(handler))

    @property
    def calls(self):
        return self.beta.messages.calls


def osint_handler(allowed_url: str):
    """Mensimulasikan 3 panggilan: riset web, afiliasi (JSON), ringkasan (JSON)."""

    def handle(kwargs, n):
        if kwargs.get("tools"):
            return msg(
                NS(
                    type="web_search_tool_result",
                    content=[NS(url="https://news.example/budi", title="Berita Budi")],
                ),
                text(
                    "Budi adalah brand ambassador Kopi Senja.",
                    [NS(url="https://news.example/budi", title="Berita", cited_text="ambassador")],
                ),
            )
        schema = kwargs["output_config"]["format"]["schema"]
        if "affiliations" in schema["properties"]:
            return msg(
                text(
                    json.dumps(
                        {
                            "affiliations": [
                                {
                                    "entity_name": "PT Kopi Senja",
                                    "category": "company",
                                    "relationship": "brand ambassador",
                                    "confidence": 1.7,
                                    "rationale": "Disebut di berita",
                                    "evidence": [
                                        {"url": "https://news.example/budi", "quote": "ambassador"},
                                        {"url": "https://dibuat-buat.example", "quote": "x"},
                                    ],
                                },
                                {
                                    "entity_name": "Partai Fiktif",
                                    "category": "party",
                                    "relationship": "pendukung",
                                    "confidence": 0.4,
                                    "rationale": "tanpa bukti",
                                    "evidence": [
                                        {"url": "https://halusinasi.example", "quote": "-"}
                                    ],
                                },
                            ],
                            "caveats": ["Data terbatas"],
                        }
                    )
                )
            )
        return msg(
            text(
                json.dumps(
                    {
                        "summary": "Ringkasan.",
                        "topics": [
                            {
                                "topic": "Keamanan digital",
                                "share_percent": 60,
                                "sentiment": "positif",
                                "example_urls": [allowed_url, "https://palsu.example"],
                            }
                        ],
                        "notable_activities": [{"url": "https://palsu.example", "reason": "x"}],
                        "risk_notes": [],
                    }
                )
            )
        )

    return handle
