from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


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
