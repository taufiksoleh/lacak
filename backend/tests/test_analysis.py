from datetime import UTC, datetime, timedelta

from app.analysis.activity import activity_stats
from app.analysis.entities import AccountData, ActivityData, EntityDef, match_entities
from app.analysis.graph import interaction_graph
from app.analysis.signals import behavior_signals
from app.connectors.importer import parse_file

KOPI = EntityDef("Kopi Senja", "company", ["kopisenja_id"], ["kopisenja.example"], ["Kopi Senja"])
KOMDIGI = EntityDef("Komdigi", "government", ["kemkomdigi"], ["komdigi.go.id"], ["Komdigi"])


def test_activity_stats_uses_local_timezone():
    # 13:00 UTC Senin = 20:00 WIB Senin
    t = datetime(2026, 10, 19, 13, 0, tzinfo=UTC)
    s = activity_stats([("x", "post", t), ("x", "reply", t + timedelta(days=1))], "Asia/Jakarta")
    assert s["total"] == 2
    assert s["heatmap"][0][20] == 1 and s["heatmap"][1][20] == 1
    assert s["most_active_hour"] == 20
    assert s["by_type"] == {"post": 1, "reply": 1}


def test_entity_matching_profile_link_is_stronger_than_interactions():
    accounts = [AccountData("instagram", "budi", "kolab", ["https://www.kopisenja.example/x"], "")]
    activities = [
        ActivityData(
            "x", "repost", "RT info", "u1", [{"handle": "kemkomdigi", "kind": "repost"}], []
        )
    ]
    res = {r["entity_name"]: r for r in match_entities([KOPI, KOMDIGI], accounts, activities)}
    assert res["Kopi Senja"]["confidence"] >= 0.5
    assert res["Komdigi"]["confidence"] < 0.1
    assert "belum tentu afiliasi formal" in res["Komdigi"]["rationale"]
    assert res["Kopi Senja"]["evidence"][0]["url"] == "https://www.kopisenja.example/x"


def test_interaction_only_is_capped_below_strong():
    acts = [
        ActivityData(
            "x",
            "repost",
            "RT Komdigi https://komdigi.go.id/a",
            f"u{i}",
            [{"handle": "kemkomdigi", "kind": k}],
            ["https://komdigi.go.id/a"],
        )
        for i, k in enumerate(["repost", "mention", "quote", "reply"] * 10)
    ]
    (res,) = match_entities([KOMDIGI], [], acts)
    assert res["confidence"] == 0.45


def test_generic_go_id_domain_only_when_no_specific_entity():
    acts = [
        ActivityData("x", "post", "", "u1", [], ["https://komdigi.go.id/a"]),
        ActivityData("x", "post", "", "u2", [], ["https://pemkot-contoh.go.id/b"]),
    ]
    res = {r["entity_name"]: r for r in match_entities([KOMDIGI], [], acts)}
    generic = res["Instansi pemerintah (domain .go.id)"]
    assert [e["url"] for e in generic["evidence"]] == ["u2"]


def test_keyword_needs_word_boundary():
    acts = [ActivityData("x", "post", "Komdigiku bukan kata kunci", "u", [], [])]
    assert match_entities([KOMDIGI], [], acts) == []


def test_signals_detect_repost_heavy_duplicate_account():
    base = datetime(2026, 10, 1, 1, 0, tzinfo=UTC)
    items = [("repost", "RT @x: sama", base + timedelta(minutes=i)) for i in range(8)]
    items += [
        ("post", "teks yang sama persis berulang kali", base + timedelta(hours=i)) for i in range(4)
    ]
    s = behavior_signals(items, [base - timedelta(days=10)], "UTC")
    levels = {i["key"]: i["level"] for i in s["indicators"]}
    assert levels["repost_ratio"] == "medium"
    assert levels["duplicate_text"] == "high"
    assert levels["night_activity"] == "high"
    assert behavior_signals(items[:3], [], "UTC")["overall"] == "insufficient"


def test_graph_ranks_and_links_subject_accounts():
    g = interaction_graph(
        [("x", "budi"), ("instagram", "budi")],
        [("x", "budi", "rina", "reply")] * 3 + [("instagram", "budi", "kopisenja_id", "mention")],
        {"kopisenja_id": "Kopi Senja"},
    )
    assert g["top"][0]["handle"] == "rina" and g["top"][0]["weight"] == 3
    assert g["top"][1]["entity"] == "Kopi Senja"
    assert any(e["kinds"] == {"same_person": 1} for e in g["edges"])
    assert {n["id"] for n in g["nodes"] if n["is_subject"]} == {"x:budi", "instagram:budi"}


def test_importer_csv_and_json():
    csv_data = (
        b"platform,handle,type,text,url,created_at,targets\n"
        b"instagram,@Budi,comment,keren @rina,https://i/1,2026-10-01T10:00:00Z,comment:kopisenja_id\n"
        b"x,budi,like,x,,2026-10-01T10:00:00Z,\n"
        b"x,budi,post,x,,bukan-tanggal,\n"
    )
    rows, errors = parse_file("a.csv", csv_data)
    assert len(rows) == 1 and len(errors) == 2
    assert rows[0].handle == "budi"
    assert rows[0].activity.targets == [
        {"handle": "kopisenja_id", "kind": "comment"},
        {"handle": "rina", "kind": "mention"},
    ]
    rows, errors = parse_file(
        "a.json",
        b'{"activities":[{"platform":"threads","handle":"budi","type":"reply",'
        b'"text":"hai","created_at":"2026-10-01T10:00:00+07:00","targets":[{"handle":"@Andi","kind":"reply"}]}]}',
    )
    assert not errors and rows[0].activity.targets == [{"handle": "andi", "kind": "reply"}]
    assert rows[0].activity.created_at.hour == 3
