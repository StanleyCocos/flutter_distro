import asyncio

from fbuild_backend.services.build_worker import BuildWorker


class BuildWorkerLoop:
    def __init__(
        self,
        *,
        worker: BuildWorker | None = None,
        poll_seconds: float = 2.0,
    ) -> None:
        self._worker = worker or BuildWorker()
        self._poll_seconds = poll_seconds

    async def run_until_stopped(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            job = await asyncio.to_thread(self._worker.process_next_job)
            if job is not None:
                continue

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self._poll_seconds)
            except asyncio.TimeoutError:
                continue
