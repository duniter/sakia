import unittest
import asyncio
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.tools.decorators import asyncify, once_at_a_time, cancel_once_task


class TestDecorators(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    def test_run_only_once(self):
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

        self.lp.call_soon(lambda: task_runner.some_long_task("A", incrementer))
        self.lp.call_soon(lambda: task_runner.some_long_task("B", incrementer))
        self.lp.call_soon(lambda: task_runner.some_long_task("C", incrementer))
        self.lp.run_until_complete(exec_test())
        self.assertEqual(calls["A"], 0)
        self.assertEqual(calls["B"], 0)
        self.assertEqual(calls["C"], 1)

    def test_cancel_once(self):
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

        self.lp.call_soon(lambda: task_runner.some_long_task("A", incrementer))
        self.lp.call_soon(lambda: task_runner.some_long_task("B", incrementer))
        self.lp.call_later(1.5, lambda: task_runner.cancel_long_task())
        self.lp.run_until_complete(exec_test())
        self.assertEqual(calls["A"], 0)
        self.assertEqual(calls["B"], 1)

    def test_cancel_once_two_times(self):
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

        self.lp.call_soon(lambda: task_runner.some_long_task("A", incrementer))
        self.lp.call_soon(lambda: task_runner.some_long_task("B", incrementer))
        self.lp.call_later(1.5, lambda: task_runner.cancel_long_task())
        self.lp.call_later(2, lambda: task_runner.some_long_task("C", incrementer))
        self.lp.call_later(2, lambda: task_runner.some_long_task("D", incrementer))
        self.lp.call_later(3.5, lambda: task_runner.cancel_long_task())
        self.lp.run_until_complete(exec_test())
        self.assertEqual(calls["A"], 0)
        self.assertEqual(calls["B"], 1)
        self.assertEqual(calls["C"], 0)
        self.assertEqual(calls["D"], 1)
