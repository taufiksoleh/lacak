from app.connectors.base import Connector, ConnectorError, NotConfiguredError
from app.connectors.demo import DemoConnector
from app.connectors.instagram import InstagramConnector
from app.connectors.threads import ThreadsConnector
from app.connectors.x import XConnector
from app.connectors.youtube import YouTubeConnector

CONNECTORS: dict[str, type[Connector]] = {
    "instagram": InstagramConnector,
    "threads": ThreadsConnector,
    "x": XConnector,
    "youtube": YouTubeConnector,
}


def get_connector(platform: str, demo: bool = False) -> Connector:
    if demo:
        return DemoConnector(platform)
    return CONNECTORS[platform]()


__all__ = [
    "CONNECTORS",
    "Connector",
    "ConnectorError",
    "DemoConnector",
    "NotConfiguredError",
    "get_connector",
]
