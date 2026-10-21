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


class InstagramConnector(Connector):
    platform = "instagram"
    limitations = (
        "Instagram Graph API (Business Discovery): hanya akun Business/Creator. Akun pribadi, "
        "komentar yang ditulis akun di postingan orang lain, dan story tidak tersedia."
    )

    def is_configured(self) -> bool:
        s = get_settings()
        return bool(s.meta_access_token and s.ig_business_account_id)

    async def _discover(self, handle: str, limit: int = 0) -> dict:
        s = get_settings()
        fields = "username,name,biography,website,followers_count,follows_count,media_count"
        if limit:
            fields += (
                f",media.limit({min(limit, 100)})"
                "{id,caption,timestamp,permalink,media_type,like_count,comments_count}"
            )
        data = await self._get_json(
            f"https://graph.facebook.com/{s.graph_api_version}/{s.ig_business_account_id}",
            params={
                "fields": f"business_discovery.username({handle}){{{fields}}}",
                "access_token": s.meta_access_token,
            },
        )
        bd = data.get("business_discovery")
        if not bd:
            raise ConnectorError(
                f"instagram: @{handle} tidak ditemukan atau bukan akun Business/Creator"
            )
        return bd

    async def fetch_profile(self, handle: str) -> NormalizedProfile:
        bd = await self._discover(handle)
        bio = bd.get("biography", "")
        links = ([bd["website"]] if bd.get("website") else []) + extract_urls(bio)
        return NormalizedProfile(
            platform=self.platform,
            handle=bd.get("username", handle),
            external_id=bd.get("id", ""),
            display_name=bd.get("name", ""),
            bio=bio,
            profile_url=f"https://www.instagram.com/{bd.get('username', handle)}/",
            links=list(dict.fromkeys(links)),
            followers=bd.get("followers_count"),
            following=bd.get("follows_count"),
        )

    async def fetch_activity(
        self, profile: NormalizedProfile, limit: int
    ) -> list[NormalizedActivity]:
        bd = await self._discover(profile.handle, limit)
        out = []
        for m in bd.get("media", {}).get("data", []):
            created = parse_iso(m.get("timestamp"))
            if not created:
                continue
            caption = m.get("caption", "") or ""
            out.append(
                NormalizedActivity(
                    platform=self.platform,
                    type="post",
                    created_at=created,
                    text=caption,
                    url=m.get("permalink", ""),
                    external_id=m.get("id", ""),
                    targets=mention_targets(caption, profile.handle),
                    links=extract_urls(caption),
                    metrics={
                        "likes": m.get("like_count"),
                        "comments": m.get("comments_count"),
                        "media_type": m.get("media_type"),
                    },
                )
            )
        return out[:limit]
