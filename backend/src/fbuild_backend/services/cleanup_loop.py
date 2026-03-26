import asyncio

from fbuild_backend.services.cleanup import cleanup_runtime_files


class CleanupLoop:
    def __init__(self, *, poll_seconds: float = 3600.0) -> None:
        self._poll_seconds = poll_seconds

    async def run_until_stopped(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            await asyncio.to_thread(cleanup_runtime_files)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self._poll_seconds)
            except asyncio.TimeoutError:
                continue
