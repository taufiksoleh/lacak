from app.services import collector
from tests.fakes import FakeClient, osint_handler

DEMO = {
    "title": "Demo Budi",
    "subject_name": "Budi",
    "purpose": "Uji coba pelacakan aktivitas publik untuk keamanan internet",
    "demo": True,
    "accounts": [
        {"platform": "x", "handle": "@budi_demo"},
        {"platform": "instagram", "handle": "budi_demo"},
    ],
}


def test_purpose_is_required(client):
    r = client.post("/api/investigations", json={**DEMO, "purpose": "singkat"})
    assert r.status_code == 422


def test_demo_flow_without_ai(client):
    r = client.post("/api/investigations", json=DEMO)
    assert r.status_code == 201, r.text
    inv = r.json()
    assert [a["handle"] for a in inv["accounts"]] == ["budi_demo", "budi_demo"]

    r = client.post(f"/api/investigations/{inv['id']}/collect")
    assert r.status_code == 202
    inv = client.get(f"/api/investigations/{inv['id']}").json()
    assert inv["status"] == "done", inv["status_detail"]
    assert inv["analysis"]["stats"]["total"] > 0
    assert inv["analysis"]["ai"] is None

    tl = client.get(f"/api/investigations/{inv['id']}/timeline?platform=x&limit=5").json()
    assert tl["total"] > 0 and len(tl["items"]) == 5
    assert all(i["platform"] == "x" for i in tl["items"])

    names = [
        f["entity_name"] for f in client.get(f"/api/investigations/{inv['id']}/affiliations").json()
    ]
    assert "PT Kopi Senja Nusantara (contoh fiktif)" in names
    assert names[0] == "PT Kopi Senja Nusantara (contoh fiktif)"

    graph = client.get(f"/api/investigations/{inv['id']}/graph").json()
    assert any(n["entity"] for n in graph["nodes"])

    report = client.get(f"/api/investigations/{inv['id']}/report").json()
    assert report["findings"] and report["recent_activities"] and report["limitations"]

    actions = [a["action"] for a in client.get(f"/api/audit?investigation_id={inv['id']}").json()]
    assert {"create", "collect_start", "collect", "report_view"} <= set(actions)


def test_unconfigured_connectors_report_error(client):
    inv = client.post("/api/investigations", json={**DEMO, "demo": False}).json()
    client.post(f"/api/investigations/{inv['id']}/collect")
    inv = client.get(f"/api/investigations/{inv['id']}").json()
    assert inv["status"] == "done"
    assert "belum dikonfigurasi" in inv["accounts"][0]["error"]


def test_import_creates_accounts_and_reanalyzes(client):
    inv = client.post("/api/investigations", json={**DEMO, "demo": False}).json()
    csv = (
        "platform,handle,type,text,url,created_at,targets\n"
        "youtube,budi_yt,comment,Mantap @kopisenja_id,https://y/1,2026-10-01T10:00:00Z,\n"
        "x,budi_demo,reply,setuju,https://x/2,2026-10-02T10:00:00Z,reply:kemkomdigi\n"
    )
    r = client.post(
        f"/api/investigations/{inv['id']}/import",
        files={"file": ("data.csv", csv, "text/csv")},
    )
    assert r.json() == {"imported": 2, "skipped": 0, "errors": []}
    inv = client.get(f"/api/investigations/{inv['id']}").json()
    assert {a["handle"] for a in inv["accounts"]} == {"budi_demo", "budi_yt"}
    assert inv["analysis"]["stats"]["total"] == 2


async def test_collect_with_ai(client):
    inv = client.post("/api/investigations", json=DEMO).json()
    fake = FakeClient(osint_handler("https://example.com/x/budi_demo/0"))
    await collector.collect(inv["id"], ai_client=fake)
    assert len(fake.calls) == 3
    inv = client.get(f"/api/investigations/{inv['id']}").json()
    assert inv["status"] == "done"
    ai = inv["analysis"]["ai"]
    assert ai["summary"] == "Ringkasan."
    assert ai["topics"][0]["example_urls"] == ["https://example.com/x/budi_demo/0"]
    assert ai["notable_activities"] == []
    findings = client.get(f"/api/investigations/{inv['id']}/affiliations").json()
    assert any(f["method"] == "ai" and f["entity_name"] == "PT Kopi Senja" for f in findings)
    assert not any(f["entity_name"] == "Partai Fiktif" for f in findings)
    web = client.get(f"/api/investigations/{inv['id']}/web-findings").json()
    assert web[0]["url"] == "https://news.example/budi"


def test_entities_and_delete(client):
    r = client.post(
        "/api/entities",
        json={
            "name": "Contoh LSM",
            "category": "ngo",
            "handles": ["@Contoh"],
            "domains": [" lsm.example "],
        },
    )
    assert r.status_code == 201 and r.json()["handles"] == ["contoh"]
    assert r.json()["domains"] == ["lsm.example"]
    assert (
        client.post("/api/entities", json={"name": "Contoh LSM", "category": "ngo"}).status_code
        == 409
    )
    inv = client.post("/api/investigations", json=DEMO).json()
    assert client.delete(f"/api/investigations/{inv['id']}").status_code == 204
    assert client.get(f"/api/investigations/{inv['id']}").status_code == 404
    status = client.get("/api/connectors/status").json()
    assert {c["platform"] for c in status["connectors"]} == {"instagram", "threads", "x", "youtube"}
    assert status["ai"]["configured"] is False
