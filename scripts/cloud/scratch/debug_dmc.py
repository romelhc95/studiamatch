import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def main():
    url = "https://dmc.pe/"
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
        async with session.get(url, timeout=10) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            for a in soup.find_all('a', href=True):
                links.append(a['href'])
            print(f"Found {len(links)} links. First 10: {links[:10]}")

asyncio.run(main())
