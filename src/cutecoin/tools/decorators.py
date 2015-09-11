import asyncio
import functools


def asyncify(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        asyncio.async(asyncio.coroutine(fn)(*args, **kwargs))

    return wrapper
