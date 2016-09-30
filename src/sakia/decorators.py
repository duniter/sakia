import asyncio
import functools
import logging


def cancel_once_task(object, fn):
    if getattr(object, "__tasks", None):
        tasks = getattr(object, "__tasks")
        if fn.__name__ in tasks and not tasks[fn.__name__].done():
            logging.debug("Cancelling {0} ".format(fn.__name__))
            getattr(object, "__tasks")[fn.__name__].cancel()


def once_at_a_time(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        def task_done(task):
            try:
                func_call = args[0].__tasks[fn.__name__]
                args[0].__tasks.pop(fn.__name__)
                if getattr(func_call, "_next_task", None):
                    start_task(func_call._next_task[0],
                               *func_call._next_task[1],
                               **func_call._next_task[2])
            except KeyError:
                logging.debug("Task {0} already removed".format(fn.__name__))

        def start_task(f, *a, **k):
            args[0].__tasks[f.__name__] = f(*a, **k)
            args[0].__tasks[f.__name__].add_done_callback(task_done)

        if getattr(args[0], "__tasks", None) is None:
            setattr(args[0], "__tasks", {})

        if fn.__name__ in args[0].__tasks:
            args[0].__tasks[fn.__name__]._next_task = (fn, args, kwargs)
            args[0].__tasks[fn.__name__].cancel()
        else:
            start_task(fn, *args, **kwargs)

        return args[0].__tasks[fn.__name__]
    return wrapper


def asyncify(fn):
    """
    Instanciates a coroutine in a task
    :param fn: the coroutine to run
    :return: the task
    :rtype: asyncio.Task
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return asyncio.ensure_future(asyncio.coroutine(fn)(*args, **kwargs))

    return wrapper
