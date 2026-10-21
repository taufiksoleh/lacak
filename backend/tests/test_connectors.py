import httpx
import pytest
import respx

from app.config import get_settings
from app.connectors import NotConfiguredError
from app.connectors.instagram import InstagramConnector
from app.connectors.threads import ThreadsConnector
from app.connectors.x import XConnector
from app.connectors.youtube import YouTubeConnector


def configure(monkeypatch, **env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()


@respx.mock
async def test_x_connector_normalizes_reply_repost_mentions(monkeypatch):
    configure(monkeypatch, X_BEARER_TOKEN="tok")
    respx.get("https://api.x.com/2/users/by/username/budi").respond(
        json={
            "data": {
                "id": "1",
                "username": "budi",
                "name": "Budi",
                "description": "Staf @kemkomdigi",
                "created_at": "2020-01-01T00:00:00.000Z",
                "public_metrics": {"followers_count": 10, "following_count": 5},
                "entities": {"url": {"urls": [{"expanded_url": "https://komdigi.go.id"}]}},
            }
        }
    )
    tweets = respx.get("https://api.x.com/2/users/1/tweets").respond(
        json={
            "data": [
                {
                    "id": "10",
                    "text": "RT @kemkomdigi: Waspada hoaks",
                    "created_at": "2026-10-01T12:00:00.000Z",
                    "referenced_tweets": [{"type": "retweeted", "id": "99"}],
                    "entities": {"mentions": [{"username": "kemkomdigi"}]},
                },
                {
                    "id": "11",
                    "text": "@andi setuju @rina",
                    "created_at": "2026-10-02T12:00:00.000Z",
                    "in_reply_to_user_id": "7",
                    "referenced_tweets": [{"type": "replied_to", "id": "98"}],
                    "entities": {"mentions": [{"username": "andi"}, {"username": "rina"}]},
                },
            ],
            "includes": {
                "users": [{"id": "5", "username": "kemkomdigi"}, {"id": "7", "username": "andi"}],
                "tweets": [{"id": "99", "author_id": "5"}],
            },
            "meta": {},
        }
    )
    c = XConnector(httpx.AsyncClient())
    p = await c.fetch_profile("budi")
    assert p.links == ["https://komdigi.go.id"]
    acts = await c.fetch_activity(p, 50)
    assert tweets.calls[0].request.headers["authorization"] == "Bearer tok"
    assert acts[0].type == "repost"
    assert acts[0].targets == [{"handle": "kemkomdigi", "kind": "repost"}]
    assert acts[1].type == "reply"
    assert acts[1].targets == [
        {"handle": "andi", "kind": "reply"},
        {"handle": "rina", "kind": "mention"},
    ]


@respx.mock
async def test_youtube_connector(monkeypatch):
    configure(monkeypatch, YOUTUBE_API_KEY="k")
    respx.get("https://www.googleapis.com/youtube/v3/channels").respond(
        json={
            "items": [
                {
                    "id": "UCabc",
                    "snippet": {
                        "title": "Budi TV",
                        "description": "Kerja sama: https://kopisenja.example",
                        "customUrl": "@buditv",
                        "publishedAt": "2019-05-01T00:00:00Z",
                    },
                    "statistics": {"subscriberCount": "1234"},
                    "contentDetails": {"relatedPlaylists": {"uploads": "UUabc"}},
                }
            ]
        }
    )
    respx.get("https://www.googleapis.com/youtube/v3/playlistItems").respond(
        json={
            "items": [
                {
                    "snippet": {
                        "title": "Review",
                        "description": "bareng @kopisenja_id",
                        "publishedAt": "2026-10-01T10:00:00Z",
                        "resourceId": {"videoId": "v1"},
                    }
                }
            ]
        }
    )
    c = YouTubeConnector(httpx.AsyncClient())
    p = await c.fetch_profile("buditv")
    assert p.followers == 1234 and p.handle == "buditv"
    acts = await c.fetch_activity(p, 10)
    assert acts[0].url == "https://www.youtube.com/watch?v=v1"
    assert acts[0].targets == [{"handle": "kopisenja_id", "kind": "mention"}]


@respx.mock
async def test_instagram_and_threads(monkeypatch):
    configure(
        monkeypatch, META_ACCESS_TOKEN="m", IG_BUSINESS_ACCOUNT_ID="17", THREADS_ACCESS_TOKEN="t"
    )
    respx.get(url__regex=r"https://graph\.facebook\.com/.*/17").respond(
        json={
            "business_discovery": {
                "id": "9",
                "username": "budi",
                "biography": "hai",
                "website": "https://kopisenja.example",
                "followers_count": 50,
                "media": {
                    "data": [
                        {
                            "id": "m1",
                            "caption": "kolab @kopisenja_id",
                            "timestamp": "2026-10-01T10:00:00+0000",
                            "permalink": "https://instagram.com/p/1",
                        }
                    ]
                },
            }
        }
    )
    respx.get("https://graph.threads.net/v1.0/profile_lookup").respond(
        json={"username": "budi", "name": "Budi", "biography": "", "follower_count": 3}
    )
    respx.get("https://graph.threads.net/v1.0/profile_posts").respond(
        json={"data": [{"id": "t1", "text": "halo @rina", "timestamp": "2026-10-01T10:00:00+0000"}]}
    )
    ig = InstagramConnector(httpx.AsyncClient())
    p = await ig.fetch_profile("budi")
    assert p.links == ["https://kopisenja.example"]
    assert (await ig.fetch_activity(p, 10))[0].targets[0]["handle"] == "kopisenja_id"
    th = ThreadsConnector(httpx.AsyncClient())
    tp = await th.fetch_profile("budi")
    assert (await th.fetch_activity(tp, 10))[0].targets == [{"handle": "rina", "kind": "mention"}]


async def test_unconfigured_connector_raises():
    c = XConnector(httpx.AsyncClient())
    assert not c.is_configured()
    with pytest.raises(NotConfiguredError):
        await c.fetch_profile("budi")
