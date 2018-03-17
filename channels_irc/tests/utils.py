import asyncio


def async_test(coro):
    """
    Async test wrapper courtesy of: https://stackoverflow.com/a/23036785/3362468
    """
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper
