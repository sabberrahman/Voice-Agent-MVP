import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("voxagent.errors")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "correlation_id": getattr(request.state, "correlation_id", None),
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "correlation_id": getattr(request.state, "correlation_id", None),
            },
        )
