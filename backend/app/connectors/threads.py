from app.config import get_settings
from app.connectors.base import (
    Connector,
    ConnectorError,
    NormalizedActivity,
    NormalizedProfile,
    extract_urls,
    mention_targets,
)
from app.timeutil import parse_iso

API = "https://graph.threads.net/v1.0"


class ThreadsConnector(Connector):
    platform = "threads"
    limitations = (
        "Threads API (izin threads_profile_discovery): profil publik dan postingan publik. "
        "Balasan yang ditulis akun di thread orang lain tidak selalu tersedia."
    )

    def is_configured(self) -> bool:
        return bool(get_settings().threads_access_token)

    def _token(self) -> dict:
        return {"access_token": get_settings().threads_access_token}

    async def fetch_profile(self, handle: str) -> NormalizedProfile:
        data = await self._get_json(
            f"{API}/profile_lookup",
            params={
                "username": handle,
                "fields": "username,name,biography,is_verified,follower_count",
                **self._token(),
            },
        )
        if not data.get("username"):
            raise ConnectorError(f"threads: akun @{handle} tidak ditemukan")
        bio = data.get("biography", "")
        return NormalizedProfile(
            platform=self.platform,
            handle=data["username"],
            display_name=data.get("name", ""),
            bio=bio,
            profile_url=f"https://www.threads.net/@{data['username']}",
            links=extract_urls(bio),
            followers=data.get("follower_count"),
            verified=bool(data.get("is_verified")),
        )

    async def fetch_activity(
        self, profile: NormalizedProfile, limit: int
    ) -> list[NormalizedActivity]:
        data = await self._get_json(
            f"{API}/profile_posts",
            params={
                "username": profile.handle,
                "fields": "id,text,timestamp,permalink,media_type,is_quote_post",
                "limit": min(limit, 100),
                **self._token(),
            },
        )
        out = []
        for p in data.get("data", []):
            created = parse_iso(p.get("timestamp"))
            if not created:
                continue
            text = p.get("text", "") or ""
            out.append(
                NormalizedActivity(
                    platform=self.platform,
                    type="quote" if p.get("is_quote_post") else "post",
                    created_at=created,
                    text=text,
                    url=p.get("permalink", ""),
                    external_id=p.get("id", ""),
                    targets=mention_targets(text, profile.handle),
                    links=extract_urls(text),
                )
            )
        return out[:limit]
