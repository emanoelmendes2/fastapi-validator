"""Decorators para validação de requests e responses."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError as PydanticValidationError

from .exceptions import ValidationError
from .validators import Validator

F = TypeVar("F", bound=Callable[..., Any])

__all__ = [
    "validate_request",
    "validate_response",
]


def validate_request(
    validators: dict[str, Validator] | None = None,
    model: type[BaseModel] | None = None,
) -> Callable[[F], F]:
    """
    Decorator para validar dados de request.

    Args:
        validators: Dicionário mapeando nomes de campos para validadores
        model: Modelo Pydantic para validação adicional

    Example:
        @app.post("/users")
        @validate_request(validators={"email": EmailValidator()})
        async def create_user(email: str):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            errors: list[dict[str, Any]] = []

            # Valida com validators customizados
            if validators:
                for field_name, validator in validators.items():
                    if field_name in kwargs:
                        try:
                            kwargs[field_name] = validator.validate(
                                kwargs[field_name], field_name
                            )
                        except ValidationError as e:
                            errors.append(e.to_dict())

            # Valida com modelo Pydantic
            if model:
                try:
                    validated = model(**kwargs)
                    kwargs.update(validated.model_dump())
                except PydanticValidationError as e:
                    for error in e.errors():
                        errors.append({
                            "field": ".".join(str(loc) for loc in error["loc"]),
                            "message": error["msg"],
                            "code": error["type"],
                        })

            if errors:
                raise HTTPException(
                    status_code=422,
                    detail={"errors": errors},
                )

            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            errors: list[dict[str, Any]] = []

            if validators:
                for field_name, validator in validators.items():
                    if field_name in kwargs:
                        try:
                            kwargs[field_name] = validator.validate(
                                kwargs[field_name], field_name
                            )
                        except ValidationError as e:
                            errors.append(e.to_dict())

            if model:
                try:
                    validated = model(**kwargs)
                    kwargs.update(validated.model_dump())
                except PydanticValidationError as e:
                    for error in e.errors():
                        errors.append({
                            "field": ".".join(str(loc) for loc in error["loc"]),
                            "message": error["msg"],
                            "code": error["type"],
                        })

            if errors:
                raise HTTPException(
                    status_code=422,
                    detail={"errors": errors},
                )

            return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def validate_response(
    model: type[BaseModel] | None = None,
    validators: dict[str, Validator] | None = None,
) -> Callable[[F], F]:
    """
    Decorator para validar dados de response.

    Args:
        model: Modelo Pydantic para validação do response
        validators: Validadores customizados para campos específicos

    Example:
        @app.get("/users/{user_id}")
        @validate_response(model=UserResponse)
        async def get_user(user_id: int):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            return _validate_result(result, model, validators)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            return _validate_result(result, model, validators)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def _validate_result(
    result: Any,
    model: type[BaseModel] | None,
    validators: dict[str, Validator] | None,
) -> Any:
    """Valida o resultado de uma função."""
    if result is None:
        return result

    data = result
    if isinstance(result, BaseModel):
        data = result.model_dump()

    if validators and isinstance(data, dict):
        for field_name, validator in validators.items():
            if field_name in data:
                try:
                    data[field_name] = validator.validate(data[field_name], field_name)
                except ValidationError as e:
                    raise HTTPException(
                        status_code=500,
                        detail={"error": "Response validation failed", "details": e.to_dict()},
                    )

    if model:
        try:
            return model(**data)
        except PydanticValidationError as e:
            raise HTTPException(
                status_code=500,
                detail={"error": "Response validation failed", "details": e.errors()},
            )

    return data