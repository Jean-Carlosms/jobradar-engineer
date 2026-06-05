from __future__ import annotations

import pytest
import requests

from tests.helpers import NETWORK_BLOCK_MESSAGE


@pytest.fixture(autouse=True)
def block_requests_network(request, monkeypatch):
    if request.node.get_closest_marker("network"):
        return

    def blocked_request(*args, **kwargs):
        raise RuntimeError(NETWORK_BLOCK_MESSAGE)

    blocked_request._jobradar_network_block = True
    monkeypatch.setattr(requests.sessions.Session, "request", blocked_request)
