import asyncio
import functools
import logging


def cancel_once_task(object, fn):
    if getattr(object, "__tasks", None):
        tasks = getattr(object, "__tasks")
        if fn.__name__ in tasks and not tasks[fn.__name__].done():
            getattr(object, "__tasks")[fn.__name__].cancel()


def once_at_a_time(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if getattr(args[0], "__tasks", None) is None:
            setattr(args[0], "__tasks", {})
        if fn.__name__ in args[0].__tasks:
            if not args[0].__tasks[fn.__name__].done():
                args[0].__tasks[fn.__name__].cancel()
        try:
            args[0].__tasks[fn.__name__] = fn(*args, **kwargs)
        except asyncio.CancelledError:
            logging.debug("Cancelled asyncified : {0}".format(fn.__name__))
        return args[0].__tasks[fn.__name__]
    return wrapper


def asyncify(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return asyncio.async(asyncio.coroutine(fn)(*args, **kwargs))

    return wrapper
