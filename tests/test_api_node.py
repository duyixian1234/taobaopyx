from unittest import mock
from taobaopyx.taobao import AsyncTaobaoAPIClient, APINode
import pytest
from datetime import datetime


@pytest.fixture
def client():
    yield AsyncTaobaoAPIClient(app_key="fake_key", app_secret="fake_secret")


@pytest.mark.asyncio
@mock.patch("taobaopyx.taobao.make_request")
async def test_api_node(mock_make_request, client: AsyncTaobaoAPIClient):
    taobao = APINode(client, "taobao")
    api = taobao.a.b.c
    assert api.path == "taobao.a.b.c"
    await api(session="session", a=1, b="b", c=datetime(2020, 1, 1))
    mock_make_request.assert_called_once_with(
        client, "taobao.a.b.c", dict(session="session", a=1, b="b", c=datetime(2020, 1, 1, 0, 0))
    )
