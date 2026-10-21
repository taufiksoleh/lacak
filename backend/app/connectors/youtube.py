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

API = "https://www.googleapis.com/youtube/v3"


class YouTubeConnector(Connector):
    platform = "youtube"
    limitations = (
        "YouTube Data API v3: profil channel dan video yang diunggah. API tidak menyediakan "
        "daftar semua komentar yang pernah ditulis sebuah akun; gunakan import untuk data itu."
    )

    def is_configured(self) -> bool:
        return bool(get_settings().youtube_api_key)

    def _key(self) -> dict:
        return {"key": get_settings().youtube_api_key}

    async def fetch_profile(self, handle: str) -> NormalizedProfile:
        params = {"part": "snippet,statistics,contentDetails", **self._key()}
        if handle.startswith("UC") and len(handle) == 24:
            params["id"] = handle
        else:
            params["forHandle"] = "@" + handle
        data = await self._get_json(f"{API}/channels", params=params)
        items = data.get("items") or []
        if not items:
            raise ConnectorError(f"youtube: channel @{handle} tidak ditemukan")
        ch = items[0]
        sn = ch.get("snippet", {})
        stats = ch.get("statistics", {})
        desc = sn.get("description", "")
        custom = (sn.get("customUrl") or "@" + handle).lstrip("@")
        return NormalizedProfile(
            platform=self.platform,
            handle=custom,
            external_id=ch["id"],
            display_name=sn.get("title", ""),
            bio=desc,
            profile_url=f"https://www.youtube.com/@{custom}",
            links=extract_urls(desc),
            followers=int(stats["subscriberCount"]) if stats.get("subscriberCount") else None,
            created_at=parse_iso(sn.get("publishedAt")),
            raw={
                "uploads": ch.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
            },
        )

    async def fetch_activity(
        self, profile: NormalizedProfile, limit: int
    ) -> list[NormalizedActivity]:
        playlist = profile.raw.get("uploads")
        if not playlist:
            return []
        out: list[NormalizedActivity] = []
        page_token = None
        while len(out) < limit:
            params = {
                "part": "snippet",
                "playlistId": playlist,
                "maxResults": min(50, limit - len(out)),
                **self._key(),
            }
            if page_token:
                params["pageToken"] = page_token
            data = await self._get_json(f"{API}/playlistItems", params=params)
            for item in data.get("items", []):
                sn = item.get("snippet", {})
                vid = sn.get("resourceId", {}).get("videoId", "")
                text = f"{sn.get('title', '')}\n\n{sn.get('description', '')}".strip()
                created = parse_iso(sn.get("publishedAt"))
                if not created:
                    continue
                out.append(
                    NormalizedActivity(
                        platform=self.platform,
                        type="post",
                        created_at=created,
                        text=text,
                        url=f"https://www.youtube.com/watch?v={vid}" if vid else "",
                        external_id=vid,
                        targets=mention_targets(text, profile.handle),
                        links=extract_urls(text),
                    )
                )
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return out[:limit]
