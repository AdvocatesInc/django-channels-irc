import asyncio
from unittest.mock import Mock


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
