import hashlib
import hmac
import json
import logging
import time
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


def create_http_client():
    client = httpx.AsyncClient()
    return client


def default_value_to_str(val):
    return str(val)


VALUE_TO_STR = {
    datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
    str: lambda v: v,
    float: lambda v: "%.2f" % v,
    bool: lambda v: str(v).lower(),
}


class APIRequest:
    def __init__(self, url: str, client: "AsyncTaobaoAPIClient", values: dict):
        self.url = url
        self.client = client
        self.values = values

    def sign(self):
        data, files = {}, {}
        if not self.values:
            raise NotImplementedError("no values")
        args = {
            "app_key": self.client.app_key,
            "sign_method": "hmac",
            "format": "json",
            "v": "2.0",
            "timestamp": datetime.now(),
        }
        for key, value in dict(self.values, **args).items():
            if hasattr(value, "read"):
                files[key] = value.value
            elif value is not None:
                data[key] = VALUE_TO_STR.get(type(value), default_value_to_str)(value)
        args_str = "".join(f"{key}{data[key]}" for key in sorted(data.keys()))
        sign = hmac.new(self.client.app_secret.encode(), args_str.encode(), digestmod=hashlib.md5)
        data["sign"] = sign.hexdigest().upper()
        return data, files

    async def run(self):
        data, files = self.sign()
        input_args = json.dumps(dict(data, **{key: str(value) for key, value in files.items()}), ensure_ascii=False)
        method = data.get("method", "")

        ts_start = time.time()
        ret = await self.open(data, files)
        ts_used = (time.time() - ts_start) * 1000

        output_args = json.dumps(ret, ensure_ascii=False)
        logger.debug(f"[TOP_API_CALL] {ts_used:2f}ms |xxx| {method} |xxx| {input_args} |xxx| {output_args}")

        if "error_response" in ret:
            error_resp = ret["error_response"]
            raise TaobaoAPIError(data, **error_resp)

        return ret

    async def open(self, data: dict, files: dict):
        timeout = 5
        if files:
            timeout = 20
        default_headers = {"Accept-Encoding": "gzip", "Connection": "close"}
        resp = await self.client.http_client.post(
            self.url, data=data, files=files, timeout=timeout, headers=default_headers
        )
        try:
            return resp.json()
        except ValueError:
            try:
                text = resp.text.replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")
                return json.loads(text)
            except ValueError as err:
                return {
                    "error_response": {
                        "msg": "json decode error",
                        "sub_code": "ism.json-decode-error",
                        "code": 15,
                        "sub_msg": f"json-error: {str(err)} || {resp.text}",
                    }
                }


async def make_request(client: "AsyncTaobaoAPIClient", method: str, kwargs: dict):
    kwargs["method"] = method
    request = APIRequest(client.gw_url, client, kwargs)
    return await request.run()


class TaobaoAPIError(Exception):
    """raise APIError if got failed json message."""

    def __init__(self, request, code="", msg="", sub_code="", sub_msg="", request_id="", **kwargs):
        """TaoBao SDK Error, Raised From TaoBao"""
        # pylint:disable=too-many-arguments
        self.request = request
        self.code = code
        self.msg = msg
        self.sub_code = sub_code
        self.sub_msg = sub_msg
        self.request_id = request_id
        self.kwargs = kwargs
        super().__init__(self, self.__str__())

    def __repr__(self):
        return f"{self.code}|{self.msg}|{self.sub_code}|{self.sub_msg}|{self.request_id}|{self.request}"

    def __str__(self):
        """Build String For All the Request and Response"""
        return f"{self.code}|{self.msg}|{self.sub_code}|{self.sub_msg}|{self.request_id}"


class AsyncTaobaoAPIClient:
    def __init__(
        self,
        /,
        app_key: str,
        app_secret: str,
        domain: str = "https://eco.taobao.com",
        http_client: httpx.AsyncClient = None,
        **kwargs,
    ):
        self.app_key = app_key
        self.app_secret = app_secret
        if domain.startswith("https://") or domain.startswith("http://"):
            self.gw_url = f"{domain}/router/rest"
        else:
            self.gw_url = f"http://{domain}/router/rest"
        self.kwargs = kwargs
        self.http_client = http_client or create_http_client()

    def __getattr__(self, method):
        async def wrap(**kwargs):
            return await make_request(self, method, kwargs)

        return wrap

    def __repr__(self):
        return f"AsyncTaobaoAPIClient(app_key={self.app_key})"

    async def aclose(self):
        await self.http_client.aclose()


class APINode:
    def __init__(self, client: AsyncTaobaoAPIClient, path: str):
        self.client = client
        self.path = path

    def __getattr__(self, field: str):
        return APINode(self.client, f"{self.path}.{field}")

    async def __call__(self, *args, **kwargs):
        return await getattr(self.client, self.path)(*args, **kwargs)

    def __repr__(self):
        return f"APINode(client={self.client}, method={self.path})"
