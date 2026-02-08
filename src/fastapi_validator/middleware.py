"""Middleware de validação para FastAPI."""

from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .exceptions import ValidationError, ValidatorException

__all__ = [
    "ValidationMiddleware",
]


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware que captura exceções de validação e retorna respostas formatadas.

    Example:
        from fastapi import FastAPI
        from fastapi_validator import ValidationMiddleware

        app = FastAPI()
        app.add_middleware(ValidationMiddleware)
    """

    def __init__(
        self,
        app: Any,
        error_handler: Callable[[ValidationError], dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(app)
        self.error_handler = error_handler or self._default_error_handler

    @staticmethod
    def _default_error_handler(error: ValidationError) -> dict[str, Any]:
        """Handler padrão para erros de validação."""
        return {
            "success": False,
            "error": {
                "type": "validation_error",
                "field": error.field,
                "message": error.message,
                "code": error.code,
            },
        }

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        """Processa a requisição e captura exceções de validação."""
        try:
            response = await call_next(request)
            return response
        except ValidationError as e:
            return JSONResponse(
                status_code=422,
                content=self.error_handler(e),
            )
        except ValidatorException as e:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": {
                        "type": "validator_error",
                        "message": e.message,
                        "details": e.details,
                    },
                },
            )