import pytest
import requests

from tests.helpers import NETWORK_BLOCK_MESSAGE


def test_network_access_is_blocked_by_default():
    with pytest.raises(RuntimeError, match=NETWORK_BLOCK_MESSAGE):
        requests.get("https://example.com", timeout=1)


@pytest.mark.network
def test_network_marker_disables_default_requests_guard():
    assert not getattr(requests.sessions.Session.request, "_jobradar_network_block", False)
