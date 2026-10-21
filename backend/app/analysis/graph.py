from collections import defaultdict

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities


def interaction_graph(
    subjects: list[tuple[str, str]],
    interactions: list[tuple[str, str, str, str]],
    entity_handles: dict[str, str],
    top_n: int = 60,
) -> dict:
    """subjects: (platform, handle) akun target.
    interactions: (platform, subject_handle, other_handle, kind).
    entity_handles: handle -> nama entitas (untuk menandai node)."""
    weights: dict[tuple[str, str], dict] = defaultdict(lambda: {"weight": 0, "kinds": {}})
    for platform, subj, other, kind in interactions:
        key = (f"{platform}:{subj.lower()}", f"{platform}:{other.lower()}")
        w = weights[key]
        w["weight"] += 1
        w["kinds"][kind] = w["kinds"].get(kind, 0) + 1

    # Peringkat akun terkait berdasarkan total bobot (lintas platform digabung per handle)
    totals: dict[str, dict] = {}
    for (_, tgt), w in weights.items():
        platform, handle = tgt.split(":", 1)
        t = totals.setdefault(
            handle, {"handle": handle, "weight": 0, "platforms": set(), "kinds": defaultdict(int)}
        )
        t["weight"] += w["weight"]
        t["platforms"].add(platform)
        for k, c in w["kinds"].items():
            t["kinds"][k] += c
    top = sorted(totals.values(), key=lambda t: t["weight"], reverse=True)
    keep = {t["handle"] for t in top[:top_n]}

    g = nx.Graph()
    subject_ids = {f"{p}:{h.lower()}" for p, h in subjects}
    for sid in subject_ids:
        g.add_node(sid)
    edges = []
    for (src, tgt), w in weights.items():
        if tgt.split(":", 1)[1] not in keep:
            continue
        g.add_edge(src, tgt, weight=w["weight"])
        edges.append({"source": src, "target": tgt, "weight": w["weight"], "kinds": w["kinds"]})

    # Akun target yang sama di beberapa platform dihubungkan agar terlihat sebagai satu orang
    subject_list = sorted(subject_ids)
    for a, b in zip(subject_list, subject_list[1:], strict=False):
        g.add_edge(a, b, weight=1)
        edges.append({"source": a, "target": b, "weight": 1, "kinds": {"same_person": 1}})

    community: dict[str, int] = {}
    if g.number_of_edges() > 1:
        for i, members in enumerate(greedy_modularity_communities(g, weight="weight")):
            for m in members:
                community[m] = i

    nodes = []
    for nid in g.nodes:
        platform, handle = nid.split(":", 1)
        nodes.append(
            {
                "id": nid,
                "label": "@" + handle,
                "platform": platform,
                "is_subject": nid in subject_ids,
                "weight": int(g.degree(nid, weight="weight")),
                "community": community.get(nid, 0),
                "entity": entity_handles.get(handle),
            }
        )
    return {
        "nodes": nodes,
        "edges": edges,
        "top": [
            {
                "handle": t["handle"],
                "weight": t["weight"],
                "platforms": sorted(t["platforms"]),
                "kinds": dict(t["kinds"]),
                "entity": entity_handles.get(t["handle"]),
            }
            for t in top[:20]
        ],
    }
