import pytest

from app.ai import affiliation, research
from app.ai.client import AIError, ask
from tests.fakes import FakeClient, msg, osint_handler, text


async def test_ask_resumes_pause_turn_and_sets_fallbacks():
    def handler(kwargs, n):
        return msg(text("sebagian"), stop="pause_turn") if n == 1 else msg(text("selesai"))

    client = FakeClient(handler)
    res = await ask(client, system="s", content="c", tools=[{"type": "web_search_20260209"}])
    assert res.content[0].text == "selesai"
    assert len(client.calls) == 2
    assert client.calls[1]["messages"][1]["role"] == "assistant"
    assert client.calls[0]["fallbacks"] == "default"
    assert client.calls[0]["betas"] == ["server-side-fallback-2026-07-01"]


async def test_ask_raises_on_refusal():
    client = FakeClient(lambda k, n: msg(stop="refusal"))
    with pytest.raises(AIError):
        await ask(client, system="s", content="c")


async def test_research_collects_cited_sources():
    client = FakeClient(osint_handler(""))
    res = await research.research(client, "Budi", [{"platform": "x", "handle": "budi"}])
    assert res["sources"] == [
        {"url": "https://news.example/budi", "title": "Berita", "snippet": "ambassador"}
    ]
    assert "<data>" in client.calls[0]["messages"][0]["content"]


async def test_affiliation_drops_unsupported_evidence_and_clamps():
    client = FakeClient(osint_handler(""))
    res = await affiliation.analyze_affiliations(client, {}, {"https://news.example/budi"})
    assert len(res["affiliations"]) == 1
    aff = res["affiliations"][0]
    assert aff["confidence"] == 1.0
    assert [e["url"] for e in aff["evidence"]] == ["https://news.example/budi"]
    assert aff["method"] == "ai"
