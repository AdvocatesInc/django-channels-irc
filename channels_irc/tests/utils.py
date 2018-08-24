import asyncio
from unittest.mock import Mock

from django.test import TestCase


def async_test(coro):
    """
    Async test wrapper courtesy of: https://stackoverflow.com/a/23036785/3362468
    """
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


def AsyncMock():
    """
    Substitute Mock for mocking/patching coroutines.  Courtesy of:
    https://stackoverflow.com/a/32505333/3362468
    """
    coro = Mock(name="CoroutineResult")
    corofunc = Mock(name="CoroutineFunction",
                    side_effect=asyncio.coroutine(coro))
    corofunc.coro = coro
    return corofunc


class AsyncTestCase(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        tasks = asyncio.gather(
            *asyncio.Task.all_tasks(loop=self.loop),
            loop=self.loop,
            return_exceptions=True
        )
        tasks.add_done_callback(lambda t: self.loop.stop())
        tasks.cancel()

        while not tasks.done() and not self.loop.is_closed():
            self.loop.run_forever()

        self.loop.close()
