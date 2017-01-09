import asyncio
import pytest
from sakia.decorators import asyncify, once_at_a_time, cancel_once_task


@pytest.mark.asyncio
async def test_run_only_once():
    class TaskRunner:
        def __init__(self):
            pass

        @once_at_a_time
        @asyncify
        async def some_long_task(self, name, callback):
            await asyncio.sleep(1)
            callback(name)

    task_runner = TaskRunner()
    calls = {'A': 0, 'B': 0, 'C': 0}

    def incrementer(name):
        nonlocal calls
        calls[name] += 1

    async def exec_test():
        await asyncio.sleep(3)

    asyncio.ensure_future(task_runner.some_long_task("A", incrementer))
    asyncio.ensure_future(task_runner.some_long_task("B", incrementer))
    asyncio.ensure_future(task_runner.some_long_task("C", incrementer))
    await exec_test()
    assert calls["A"] == 0
    assert calls["B"] == 0
    assert calls["C"] == 1


@pytest.mark.asyncio
async def test_cancel_once(application):
    class TaskRunner:
        def __init__(self):
            pass

        @once_at_a_time
        @asyncify
        async def some_long_task(self, name, callback):
            await asyncio.sleep(1)
            callback(name)
            await asyncio.sleep(1)
            callback(name)

        def cancel_long_task(self):
            cancel_once_task(self, self.some_long_task)

    task_runner = TaskRunner()
    calls = {'A': 0, 'B': 0}

    def incrementer(name):
        nonlocal calls
        calls[name] += 1

    async def exec_test():
        await asyncio.sleep(3)

    application.loop.call_soon(lambda: task_runner.some_long_task("A", incrementer))
    application.loop.call_soon(lambda: task_runner.some_long_task("B", incrementer))
    application.loop.call_later(1.5, lambda: task_runner.cancel_long_task())
    await exec_test()
    assert calls["A"] == 0
    assert calls["B"] == 1


@pytest.mark.asyncio
async def test_cancel_once_two_times(application):
    class TaskRunner:
        def __init__(self):
            pass

        @once_at_a_time
        @asyncify
        async def some_long_task(self, name, callback):
            await asyncio.sleep(1)
            callback(name)
            await asyncio.sleep(1)
            callback(name)

        def cancel_long_task(self):
            cancel_once_task(self, self.some_long_task)

    task_runner = TaskRunner()
    calls = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

    def incrementer(name):
        nonlocal calls
        calls[name] += 1

    async def exec_test():
        await asyncio.sleep(6)

    application.loop.call_soon(lambda: task_runner.some_long_task("A", incrementer))
    application.loop.call_soon(lambda: task_runner.some_long_task("B", incrementer))
    application.loop.call_later(1.5, lambda: task_runner.cancel_long_task())
    application.loop.call_later(2, lambda: task_runner.some_long_task("C", incrementer))
    application.loop.call_later(2.1, lambda: task_runner.some_long_task("D", incrementer))
    application.loop.call_later(3.5, lambda: task_runner.cancel_long_task())
    await exec_test()
    assert calls["A"] == 0
    assert calls["B"] == 1
    assert calls["C"] == 0
    assert calls["D"] == 1


@pytest.mark.asyncio
async def test_two_runners():
    class TaskRunner:
        def __init__(self, name):
            self.some_long_task(name, incrementer)

        @classmethod
        def create(cls, name):
            return cls(name)

        @once_at_a_time
        @asyncify
        async def some_long_task(self, name, callback):
            await asyncio.sleep(1)
            callback(name)
            await asyncio.sleep(1)
            callback(name)

        def cancel_long_task(self):
            cancel_once_task(self, self.some_long_task)

    calls = {'A': 0, 'B': 0, 'C': 0}

    def incrementer(name):
        nonlocal calls
        calls[name] += 1

    async def exec_test():
        tr1 = TaskRunner.create("A")
        tr2 = TaskRunner.create("B")
        tr3 = TaskRunner.create("C")
        await asyncio.sleep(1.5)
        tr1.some_long_task("A", incrementer)
        tr2.some_long_task("B", incrementer)
        tr3.some_long_task("C", incrementer)
        await asyncio.sleep(1.5)

    await exec_test()
    assert calls["A"] == 2
    assert calls["B"] == 2
    assert calls["C"] == 2
