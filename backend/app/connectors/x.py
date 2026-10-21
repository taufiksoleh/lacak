from app.config import get_settings
from app.connectors.base import (
    Connector,
    ConnectorError,
    NormalizedActivity,
    NormalizedProfile,
    extract_urls,
)
from app.timeutil import parse_iso

API = "https://api.x.com/2"
REF_KIND = {"replied_to": "reply", "retweeted": "repost", "quoted": "quote"}


class XConnector(Connector):
    platform = "x"
    limitations = (
        "X API v2 (butuh akses berbayar): tweet, reply, quote, repost, dan mention dari "
        "timeline publik akun. Like dan akun privat tidak dapat diambil."
    )

    def is_configured(self) -> bool:
        return bool(get_settings().x_bearer_token)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {get_settings().x_bearer_token}"}

    async def fetch_profile(self, handle: str) -> NormalizedProfile:
        data = await self._get_json(
            f"{API}/users/by/username/{handle}",
            params={"user.fields": "created_at,description,entities,public_metrics,url,verified"},
            headers=self._headers(),
        )
        u = data.get("data")
        if not u:
            raise ConnectorError(f"x: akun @{handle} tidak ditemukan")
        ents = u.get("entities", {})
        links = [x.get("expanded_url") for x in ents.get("url", {}).get("urls", [])]
        links += [x.get("expanded_url") for x in ents.get("description", {}).get("urls", [])]
        metrics = u.get("public_metrics", {})
        return NormalizedProfile(
            platform=self.platform,
            handle=u["username"],
            external_id=u["id"],
            display_name=u.get("name", ""),
            bio=u.get("description", ""),
            profile_url=f"https://x.com/{u['username']}",
            links=[link for link in links if link],
            followers=metrics.get("followers_count"),
            following=metrics.get("following_count"),
            verified=bool(u.get("verified")),
            created_at=parse_iso(u.get("created_at")),
        )

    async def fetch_activity(
        self, profile: NormalizedProfile, limit: int
    ) -> list[NormalizedActivity]:
        out: list[NormalizedActivity] = []
        token = None
        while len(out) < limit:
            params = {
                "max_results": max(5, min(100, limit - len(out))),
                "tweet.fields": "created_at,entities,referenced_tweets,in_reply_to_user_id,"
                "public_metrics",
                "expansions": "referenced_tweets.id.author_id,in_reply_to_user_id",
                "user.fields": "username",
            }
            if token:
                params["pagination_token"] = token
            data = await self._get_json(
                f"{API}/users/{profile.external_id}/tweets", params=params, headers=self._headers()
            )
            includes = data.get("includes", {})
            users = {u["id"]: u["username"] for u in includes.get("users", [])}
            ref_authors = {
                t["id"]: users.get(t.get("author_id", ""), "") for t in includes.get("tweets", [])
            }
            for t in data.get("data", []):
                out.append(self._normalize(t, users, ref_authors, profile.handle))
            token = data.get("meta", {}).get("next_token")
            if not token:
                break
        return out[:limit]

    def _normalize(self, t: dict, users: dict, ref_authors: dict, me: str) -> NormalizedActivity:
        kind = "post"
        targets: list[dict] = []
        for ref in t.get("referenced_tweets", []) or []:
            k = REF_KIND.get(ref.get("type"))
            if not k:
                continue
            kind = k
            author = ref_authors.get(ref.get("id"), "")
            if k == "reply" and not author:
                author = users.get(t.get("in_reply_to_user_id", ""), "")
            if author and author.lower() != me.lower():
                targets.append({"handle": author.lower(), "kind": k})
        ents = t.get("entities", {})
        for m in ents.get("mentions", []) or []:
            h = (m.get("username") or "").lower()
            if h and h != me.lower() and not any(x["handle"] == h for x in targets):
                targets.append({"handle": h, "kind": "mention"})
        links = [u.get("expanded_url") for u in ents.get("urls", []) or [] if u.get("expanded_url")]
        created = parse_iso(t.get("created_at"))
        if created is None:
            raise ConnectorError("x: tweet tanpa created_at")
        return NormalizedActivity(
            platform=self.platform,
            type=kind,
            created_at=created,
            text=t.get("text", ""),
            url=f"https://x.com/{me}/status/{t['id']}",
            external_id=t["id"],
            targets=targets,
            links=links or extract_urls(t.get("text", "")),
            metrics=t.get("public_metrics", {}),
        )
