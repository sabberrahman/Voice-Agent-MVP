import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_async(operation: Callable[[], Awaitable[T]], *, attempts: int) -> T:
    last_error: Exception | None = None
    for attempt in range(max(attempts, 1)):
        try:
            return await operation()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt + 1 >= attempts:
                break
            await asyncio.sleep(0.25 * (attempt + 1))
    assert last_error is not None
    raise last_error
