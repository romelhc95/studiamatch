class _UnavailablePlaywright:
    async def start(self):
        raise RuntimeError("Playwright is unavailable in the CA1 SSR harness")


def async_playwright():
    return _UnavailablePlaywright()
