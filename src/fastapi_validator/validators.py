"""Validadores customizados para FastAPI."""

import re
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from .exceptions import ValidationError

T = TypeVar("T")

__all__ = [
    "Validator",
    "StringValidator",
    "NumberValidator",
    "EmailValidator",
    "CPFValidator",
    "CNPJValidator",
]


class Validator(ABC):
    """Classe base abstrata para validadores."""

    @abstractmethod
    def validate(self, value: Any, field_name: str = "field") -> Any:
        """Valida um valor e retorna o valor validado ou lança ValidationError."""
        pass

    def __call__(self, value: Any, field_name: str = "field") -> Any:
        """Permite usar o validador como callable."""
        return self.validate(value, field_name)


class StringValidator(Validator):
    """Validador para strings."""

    def __init__(
        self,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        strip: bool = True,
        lowercase: bool = False,
        uppercase: bool = False,
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.strip = strip
        self.lowercase = lowercase
        self.uppercase = uppercase

    def validate(self, value: Any, field_name: str = "field") -> str:
        if not isinstance(value, str):
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ser uma string",
                value=value,
                code="invalid_type",
            )

        result = value
        if self.strip:
            result = result.strip()

        if self.lowercase:
            result = result.lower()
        elif self.uppercase:
            result = result.upper()

        if self.min_length is not None and len(result) < self.min_length:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ter no mínimo {self.min_length} caracteres",
                value=value,
                code="min_length",
            )

        if self.max_length is not None and len(result) > self.max_length:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ter no máximo {self.max_length} caracteres",
                value=value,
                code="max_length",
            )

        if self.pattern and not self.pattern.match(result):
            raise ValidationError(
                field=field_name,
                message=f"{field_name} não corresponde ao padrão esperado",
                value=value,
                code="pattern_mismatch",
            )

        return result


class NumberValidator(Validator):
    """Validador para números."""

    def __init__(
        self,
        min_value: float | None = None,
        max_value: float | None = None,
        allow_float: bool = True,
        positive_only: bool = False,
    ) -> None:
        self.min_value = min_value
        self.max_value = max_value
        self.allow_float = allow_float
        self.positive_only = positive_only

    def validate(self, value: Any, field_name: str = "field") -> int | float:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ser um número",
                value=value,
                code="invalid_type",
            )

        if not self.allow_float and isinstance(value, float) and not value.is_integer():
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ser um número inteiro",
                value=value,
                code="not_integer",
            )

        if self.positive_only and value <= 0:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ser um número positivo",
                value=value,
                code="not_positive",
            )

        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ser maior ou igual a {self.min_value}",
                value=value,
                code="min_value",
            )

        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ser menor ou igual a {self.max_value}",
                value=value,
                code="max_value",
            )

        return int(value) if not self.allow_float and isinstance(value, float) else value


class EmailValidator(Validator):
    """Validador para emails."""

    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    def __init__(self, allowed_domains: list[str] | None = None) -> None:
        self.allowed_domains = allowed_domains

    def validate(self, value: Any, field_name: str = "field") -> str:
        if not isinstance(value, str):
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ser uma string",
                value=value,
                code="invalid_type",
            )

        email = value.strip().lower()

        if not self.EMAIL_PATTERN.match(email):
            raise ValidationError(
                field=field_name,
                message=f"{field_name} não é um email válido",
                value=value,
                code="invalid_email",
            )

        if self.allowed_domains:
            domain = email.split("@")[1]
            if domain not in self.allowed_domains:
                raise ValidationError(
                    field=field_name,
                    message=f"{field_name} deve ser de um dos domínios permitidos",
                    value=value,
                    code="invalid_domain",
                )

        return email


class CPFValidator(Validator):
    """Validador para CPF brasileiro."""

    def validate(self, value: Any, field_name: str = "field") -> str:
        if not isinstance(value, str):
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ser uma string",
                value=value,
                code="invalid_type",
            )

        # Remove caracteres não numéricos
        cpf = re.sub(r"\D", "", value)

        if len(cpf) != 11:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ter 11 dígitos",
                value=value,
                code="invalid_length",
            )

        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} não é um CPF válido",
                value=value,
                code="invalid_cpf",
            )

        # Calcula primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto

        # Calcula segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto

        if cpf[-2:] != f"{digito1}{digito2}":
            raise ValidationError(
                field=field_name,
                message=f"{field_name} não é um CPF válido",
                value=value,
                code="invalid_cpf",
            )

        return cpf


class CNPJValidator(Validator):
    """Validador para CNPJ brasileiro."""

    def validate(self, value: Any, field_name: str = "field") -> str:
        if not isinstance(value, str):
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ser uma string",
                value=value,
                code="invalid_type",
            )

        # Remove caracteres não numéricos
        cnpj = re.sub(r"\D", "", value)

        if len(cnpj) != 14:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} deve ter 14 dígitos",
                value=value,
                code="invalid_length",
            )

        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} não é um CNPJ válido",
                value=value,
                code="invalid_cnpj",
            )

        # Calcula primeiro dígito verificador
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto

        # Calcula segundo dígito verificador
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto

        if cnpj[-2:] != f"{digito1}{digito2}":
            raise ValidationError(
                field=field_name,
                message=f"{field_name} não é um CNPJ válido",
                value=value,
                code="invalid_cnpj",
            )

        return cnpj