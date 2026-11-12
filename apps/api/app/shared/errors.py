import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

log = logging.getLogger(__name__)


class DomainError(Exception):
    status = 400
    code = "domain_error"

    def __init__(self, detail: str = "", *, code: str | None = None) -> None:
        super().__init__(detail or self.code)
        self.detail = detail or self.code
        if code:
            self.code = code


class ValidationFailed(DomainError):
    status = 422
    code = "validation_failed"


class Unauthorized(DomainError):
    status = 401
    code = "unauthorized"


class Forbidden(DomainError):
    status = 403
    code = "forbidden"


class NotFound(DomainError):
    status = 404
    code = "not_found"


class Conflict(DomainError):
    status = 409
    code = "conflict"


class ProblemDetails(BaseModel):
    type: str
    title: str
    status: int
    code: str
    detail: str


def problem_response(err: DomainError) -> JSONResponse:
    body = ProblemDetails(
        type=f"urn:dtmai:error:{err.code}",
        title=type(err).__name__,
        status=err.status,
        code=err.code,
        detail=err.detail,
    )
    return JSONResponse(
        body.model_dump(), status_code=err.status, media_type="application/problem+json"
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _handle(_: Request, exc: DomainError) -> JSONResponse:
        return problem_response(exc)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"loc": [str(p) for p in e["loc"]], "msg": e["msg"], "type": e["type"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            {
                "type": "urn:dtmai:error:validation_failed",
                "title": "ValidationFailed",
                "status": 422,
                "code": "validation_failed",
                "detail": "request validation failed",
                "errors": errors,
            },
            status_code=422,
            media_type="application/problem+json",
        )


class UnhandledErrorMiddleware(BaseHTTPMiddleware):
    """Turns unexpected exceptions into problem+json inside the app, so CORSMiddleware (added after) still wraps them."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception:
            log.exception("unhandled error on %s %s", request.method, request.url.path)
            return JSONResponse(
                {
                    "type": "urn:dtmai:error:internal_error",
                    "title": "InternalError",
                    "status": 500,
                    "code": "internal_error",
                    "detail": "internal server error",
                },
                status_code=500,
                media_type="application/problem+json",
            )
