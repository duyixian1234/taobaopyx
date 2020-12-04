# taobaopyx

Asyncio version of taobaopy powered by httpx

## Install

```bash
pip install -U taobaopyx
```

## Use

```python
from taobaopyx.taobao import APINode, AsyncTaobaoAPIClient
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)


client = AsyncTaobaoAPIClient(app_key="fake_key", app_secret="fake_sescret")

taobao = APINode(client, "taobao")


async def get():
    res = await taobao.mixnick.get(nick="nick")
    print(res)


async def shutdown():
    await client.aclose()


asyncio.run(get())
asyncio.run(shutdown())
```
