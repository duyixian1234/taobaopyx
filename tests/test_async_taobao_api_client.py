import asyncio
from unittest import mock

import pytest
from taobaopyx.taobao import AsyncTaobaoAPIClient


@pytest.fixture
def client():
    yield AsyncTaobaoAPIClient(
        app_key="fake_key", app_secret="fake_secret", domain="eco.taobao.com", http_client=mock.Mock()
    )


def test_client(client: AsyncTaobaoAPIClient):
    assert client.gw_url == "http://eco.taobao.com/router/rest"


@pytest.mark.asyncio
async def test_close(client: AsyncTaobaoAPIClient):
    client.http_client.aclose.return_value = asyncio.Future()
    client.http_client.aclose.return_value.set_result(None)
    await client.aclose()
    client.http_client.aclose.assert_called_once_with()