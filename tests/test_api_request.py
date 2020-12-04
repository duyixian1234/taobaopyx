from unittest import mock
from taobaopyx.taobao import AsyncTaobaoAPIClient, APIRequest, TaobaoAPIError
import pytest
from datetime import datetime
import asyncmock
import hmac
import hashlib


@pytest.fixture
def client():
    yield AsyncTaobaoAPIClient(app_key="fake_key", app_secret="fake_secret", http_client=asyncmock.AsyncMock())


@pytest.fixture
def response():
    yield {"mixnick_get_response": {"nick": "mixnick", "request_id": "xxxx"}}


@pytest.fixture
def error_response():
    yield {"error_response": {"code": 40, "msg": "Missing required arguments:nick", "request_id": "xxx"}}


@pytest.fixture
def method():
    yield "taobao.mixnick.get"


@pytest.fixture
def kwargs():
    yield dict(nick="nick")


@pytest.fixture
def now():
    yield datetime(2020, 1, 1)


@pytest.fixture
def signature(client: AsyncTaobaoAPIClient, method: str, kwargs: dict, now: datetime):
    args = {
        "app_key": client.app_key,
        "sign_method": "hmac",
        "format": "json",
        "v": "2.0",
        "timestamp": now,
    }
    kwargs = kwargs.copy()
    kwargs["method"] = method
    data = {}
    for key, value in dict(kwargs, **args).items():
        data[key] = str(value)
    args_str = "".join(f"{key}{data[key]}" for key in sorted(data.keys()))
    print(args_str)
    return hmac.new(client.app_secret.encode(), args_str.encode(), hashlib.md5).hexdigest().upper()


@pytest.mark.asyncio
@mock.patch("taobaopyx.taobao.datetime")
async def test_request(
    mock_datetime,
    client: AsyncTaobaoAPIClient,
    response: dict,
    error_response: dict,
    signature: str,
    method: str,
    kwargs: dict,
    now: datetime,
):
    mock_datetime.now.return_value = now
    request = APIRequest(client.gw_url, client, dict(method=method, **kwargs))
    data, _ = request.sign()
    assert data["sign"] == signature
    client.http_client.post.return_value = mock.Mock(json=mock.Mock(return_value=response))
    assert await request.run() == response

    client.http_client.post.return_value = mock.Mock(json=mock.Mock(return_value=error_response))
    with pytest.raises(TaobaoAPIError):
        await request.run()

    client.http_client.post.return_value = mock.Mock(json=mock.Mock(side_effect=ValueError()), text="XML")
    with pytest.raises(TaobaoAPIError):
        await request.run()