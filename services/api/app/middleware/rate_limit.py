from time import monotonic

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config.settings import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        now = monotonic()
        client = request.client.host if request.client else "unknown"
        bucket = [stamp for stamp in self.requests.get(client, []) if now - stamp < 60]
        if len(bucket) >= settings.rate_limit_per_minute:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        bucket.append(now)
        self.requests[client] = bucket
        return await call_next(request)
