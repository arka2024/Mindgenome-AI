from __future__ import annotations

from typing import Any
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class ProblemException(HTTPException):
    def __init__(
        self,
        status_code: int,
        title: str,
        detail: str,
        problem_type: str = "validation",
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.title = title
        self.problem_type = (
            problem_type
            if problem_type.startswith("http")
            else f"https://mindgenome.ai/problems/{problem_type}"
        )
        self.extra = extra or {}


class UnauthorizedException(ProblemException):
    def __init__(self, detail: str = "Authentication required.", title: str = "Unauthorized") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            title=title,
            detail=detail,
            problem_type="unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(ProblemException):
    def __init__(self, detail: str = "Access denied.", title: str = "Forbidden") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            title=title,
            detail=detail,
            problem_type="forbidden",
        )


class NotFoundException(ProblemException):
    def __init__(self, detail: str = "Resource not found.", title: str = "Not Found") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            title=title,
            detail=detail,
            problem_type="not-found",
        )


class ConflictException(ProblemException):
    def __init__(self, detail: str = "Resource conflict.", title: str = "Conflict") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            title=title,
            detail=detail,
            problem_type="conflict",
        )


class RateLimitException(ProblemException):
    def __init__(self, detail: str = "Too many requests. Please slow down.", retry_after: int = 60) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            title="Rate limit exceeded",
            detail=detail,
            problem_type="rate-limited",
            headers={"Retry-After": str(retry_after)},
        )


class ValidationProblemException(ProblemException):
    def __init__(self, detail: str = "Validation error.", extra: dict[str, Any] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Validation error",
            detail=detail,
            problem_type="validation",
            extra=extra,
        )


def problem_json_response(
    status_code: int,
    title: str,
    detail: str,
    problem_type: str,
    instance: str | None = None,
    request_id: str | None = None,
    headers: dict[str, str] | None = None,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    content: dict[str, Any] = {
        "type": problem_type if problem_type.startswith("http") else f"https://mindgenome.ai/problems/{problem_type}",
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        content["instance"] = instance
    if request_id:
        content["request_id"] = request_id
    if extra:
        content.update(extra)

    response_headers = {"Content-Type": "application/problem+json"}
    if headers:
        response_headers.update(headers)

    return JSONResponse(status_code=status_code, content=content, headers=response_headers)
