"""Dataset contoh untuk demo & test. Semua orang dan akun pribadi di sini fiktif."""

import random
from datetime import UTC, datetime, timedelta

from app.connectors.base import (
    Connector,
    NormalizedActivity,
    NormalizedProfile,
    extract_urls,
    mention_targets,
)

FRIENDS = ["rina.tech", "andi_dev", "komunitas_kopi", "sari_writes", "dimas.foto"]
TEMPLATES = [
    ("post", "Workshop keamanan siber bareng @bssn_ri hari ini, materinya daging banget!"),
    ("post", "Ngopi pagi dulu sebelum kerja ☕ produk baru dari @kopisenja_id enak pol."),
    ("post", "Ringkasan diskusi literasi digital: https://komdigi.go.id/berita/literasi-digital"),
    ("reply", "Setuju sama @rina.tech, password manager itu wajib."),
    ("reply", "@andi_dev repo-nya mantap, sudah aku star."),
    ("repost", "RT @kemkomdigi: Waspada penipuan berkedok undian, cek dulu sebelum klik tautan!"),
    ("repost", "RT @kemkomdigi: Laporkan konten hoaks melalui aduankonten.id"),
    ("quote", "Penting! @bssn_ri rilis panduan keamanan untuk UMKM."),
    ("post", "Kolaborasi konten dengan @kopisenja_id minggu depan, stay tuned!"),
    ("post", "Foto-foto event kemarin oleh @dimas.foto, keren!"),
    ("reply", "@sari_writes artikelnya bagus, boleh aku share?"),
    ("post", "Kenapa 2FA penting? Thread singkat 🧵"),
    ("post", "Meetup @komunitas_kopi sabtu ini di Bandung."),
]
BIOS = {
    "x": "Pegiat literasi digital | Brand ambassador @kopisenja_id | Opini pribadi",
    "instagram": "Content creator teknologi & kopi ☕ | kolaborasi: https://kopisenja.example",
    "threads": "Ngobrol soal keamanan internet & kopi",
    "youtube": "Channel edukasi keamanan digital. Kerja sama: https://kopisenja.example/partner",
}


class DemoConnector(Connector):
    platform = "demo"
    limitations = "Data contoh fiktif untuk demonstrasi."

    def __init__(self, platform: str, now: datetime | None = None):
        super().__init__()
        self.platform = platform
        self.now = now or datetime.now(UTC)

    def is_configured(self) -> bool:
        return True

    async def fetch_profile(self, handle: str) -> NormalizedProfile:
        bio = BIOS.get(self.platform, "")
        return NormalizedProfile(
            platform=self.platform,
            handle=handle,
            external_id=f"demo-{self.platform}-{handle}",
            display_name="Budi (Akun Demo)",
            bio=bio,
            profile_url=f"https://example.com/{self.platform}/{handle}",
            links=extract_urls(bio) or ["https://kopisenja.example"],
            followers=1200 + len(self.platform) * 311,
            following=340,
            created_at=self.now - timedelta(days=200),
        )

    async def fetch_activity(
        self, profile: NormalizedProfile, limit: int
    ) -> list[NormalizedActivity]:
        rng = random.Random(f"{self.platform}:{profile.handle}")
        n = min(limit, 60)
        out = []
        for i in range(n):
            kind, text = TEMPLATES[rng.randrange(len(TEMPLATES))]
            if self.platform != "x" and kind == "repost":
                kind = "post"
            # Pola aktif malam hari (19-23 WIB = 12-16 UTC) dengan sedikit variasi
            hour = rng.choice([12, 13, 14, 15, 16, 16, 2, 3])
            created = (self.now - timedelta(days=rng.randrange(0, 90))).replace(
                hour=hour, minute=rng.randrange(60), second=0, microsecond=0
            )
            targets = mention_targets(text, profile.handle)
            if kind in ("reply", "repost", "quote") and targets:
                targets[0] = {**targets[0], "kind": kind}
            out.append(
                NormalizedActivity(
                    platform=self.platform,
                    type=kind,
                    created_at=created,
                    text=text,
                    url=f"https://example.com/{self.platform}/{profile.handle}/{i}",
                    external_id=f"{i}",
                    targets=targets,
                    links=extract_urls(text),
                    metrics={"likes": rng.randrange(5, 300)},
                )
            )
        return sorted(out, key=lambda a: a.created_at, reverse=True)
