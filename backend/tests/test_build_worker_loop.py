import asyncio
import unittest

from fbuild_backend.services.build_worker_loop import BuildWorkerLoop


class FakeWorker:
    def __init__(self, results: list[object | None]) -> None:
        self._results = results
        self.calls = 0

    def process_next_job(self) -> object | None:
        self.calls += 1
        if self._results:
            return self._results.pop(0)
        return None


class BuildWorkerLoopTest(unittest.IsolatedAsyncioTestCase):
    async def test_loop_keeps_polling_when_jobs_are_found(self) -> None:
        stop_event = asyncio.Event()
        worker = FakeWorker(results=[object(), object(), None])
        loop = BuildWorkerLoop(worker=worker, poll_seconds=0.01)

        task = asyncio.create_task(loop.run_until_stopped(stop_event))
        await asyncio.sleep(0.03)
        stop_event.set()
        await task

        self.assertGreaterEqual(worker.calls, 3)

    async def test_loop_waits_and_stops_cleanly(self) -> None:
        stop_event = asyncio.Event()
        worker = FakeWorker(results=[None, None])
        loop = BuildWorkerLoop(worker=worker, poll_seconds=0.01)

        task = asyncio.create_task(loop.run_until_stopped(stop_event))
        await asyncio.sleep(0.02)
        stop_event.set()
        await task

        self.assertGreaterEqual(worker.calls, 1)


if __name__ == "__main__":
    unittest.main()
