from __future__ import annotations

import requests as _requests


class AsyncSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False

    async def get(self, url, impersonate=None, timeout=25):
        del impersonate
        return _requests.get(url, timeout=timeout, allow_redirects=True)
