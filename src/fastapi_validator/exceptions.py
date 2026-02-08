"""Exceções customizadas para validação."""

from typing import Any

__all__ = [
    "ValidatorException",
    "ValidationError",
]


class ValidatorException(Exception):
    """Exceção base para erros de validação."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ValidatorException):
    """Exceção lançada quando uma validação falha."""

    def __init__(
        self,
        field: str,
        message: str,
        value: Any = None,
        code: str = "validation_error",
    ) -> None:
        self.field = field
        self.value = value
        self.code = code
        details = {
            "field": field,
            "value": value,
            "code": code,
        }
        super().__init__(message, details)

    def to_dict(self) -> dict[str, Any]:
        """Converte o erro para um dicionário."""
        return {
            "field": self.field,
            "message": self.message,
            "code": self.code,
        }