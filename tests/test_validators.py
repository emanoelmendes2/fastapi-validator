"""Testes para os validadores."""

import pytest

from fastapi_validator import (
    CNPJValidator,
    CPFValidator,
    EmailValidator,
    NumberValidator,
    StringValidator,
    ValidationError,
)


class TestStringValidator:
    """Testes para StringValidator."""

    def test_valid_string(self) -> None:
        validator = StringValidator()
        assert validator.validate("hello") == "hello"

    def test_strip_whitespace(self) -> None:
        validator = StringValidator(strip=True)
        assert validator.validate("  hello  ") == "hello"

    def test_min_length(self) -> None:
        validator = StringValidator(min_length=5)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("hi")
        assert exc_info.value.code == "min_length"

    def test_max_length(self) -> None:
        validator = StringValidator(max_length=5)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("hello world")
        assert exc_info.value.code == "max_length"

    def test_pattern(self) -> None:
        validator = StringValidator(pattern=r"^\d+$")
        assert validator.validate("123") == "123"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("abc")
        assert exc_info.value.code == "pattern_mismatch"

    def test_lowercase(self) -> None:
        validator = StringValidator(lowercase=True)
        assert validator.validate("HELLO") == "hello"

    def test_uppercase(self) -> None:
        validator = StringValidator(uppercase=True)
        assert validator.validate("hello") == "HELLO"

    def test_invalid_type(self) -> None:
        validator = StringValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(123)
        assert exc_info.value.code == "invalid_type"


class TestNumberValidator:
    """Testes para NumberValidator."""

    def test_valid_integer(self) -> None:
        validator = NumberValidator()
        assert validator.validate(42) == 42

    def test_valid_float(self) -> None:
        validator = NumberValidator()
        assert validator.validate(3.14) == 3.14

    def test_min_value(self) -> None:
        validator = NumberValidator(min_value=10)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(5)
        assert exc_info.value.code == "min_value"

    def test_max_value(self) -> None:
        validator = NumberValidator(max_value=10)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(15)
        assert exc_info.value.code == "max_value"

    def test_positive_only(self) -> None:
        validator = NumberValidator(positive_only=True)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(-5)
        assert exc_info.value.code == "not_positive"

    def test_disallow_float(self) -> None:
        validator = NumberValidator(allow_float=False)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(3.14)
        assert exc_info.value.code == "not_integer"

    def test_invalid_type(self) -> None:
        validator = NumberValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("42")
        assert exc_info.value.code == "invalid_type"


class TestEmailValidator:
    """Testes para EmailValidator."""

    def test_valid_email(self) -> None:
        validator = EmailValidator()
        assert validator.validate("user@example.com") == "user@example.com"

    def test_email_lowercase(self) -> None:
        validator = EmailValidator()
        assert validator.validate("User@Example.COM") == "user@example.com"

    def test_invalid_email(self) -> None:
        validator = EmailValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("invalid-email")
        assert exc_info.value.code == "invalid_email"

    def test_allowed_domains(self) -> None:
        validator = EmailValidator(allowed_domains=["company.com"])
        assert validator.validate("user@company.com") == "user@company.com"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("user@other.com")
        assert exc_info.value.code == "invalid_domain"


class TestCPFValidator:
    """Testes para CPFValidator."""

    def test_valid_cpf(self) -> None:
        validator = CPFValidator()
        # CPF válido para testes
        assert validator.validate("529.982.247-25") == "52998224725"

    def test_cpf_only_numbers(self) -> None:
        validator = CPFValidator()
        assert validator.validate("52998224725") == "52998224725"

    def test_invalid_cpf_length(self) -> None:
        validator = CPFValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("123456789")
        assert exc_info.value.code == "invalid_length"

    def test_invalid_cpf_all_same_digits(self) -> None:
        validator = CPFValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("11111111111")
        assert exc_info.value.code == "invalid_cpf"

    def test_invalid_cpf_checksum(self) -> None:
        validator = CPFValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("12345678901")
        assert exc_info.value.code == "invalid_cpf"


class TestCNPJValidator:
    """Testes para CNPJValidator."""

    def test_valid_cnpj(self) -> None:
        validator = CNPJValidator()
        # CNPJ válido para testes
        assert validator.validate("11.222.333/0001-81") == "11222333000181"

    def test_cnpj_only_numbers(self) -> None:
        validator = CNPJValidator()
        assert validator.validate("11222333000181") == "11222333000181"

    def test_invalid_cnpj_length(self) -> None:
        validator = CNPJValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("1234567890123")
        assert exc_info.value.code == "invalid_length"

    def test_invalid_cnpj_all_same_digits(self) -> None:
        validator = CNPJValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("11111111111111")
        assert exc_info.value.code == "invalid_cnpj"

    def test_invalid_cnpj_checksum(self) -> None:
        validator = CNPJValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("12345678901234")
        assert exc_info.value.code == "invalid_cnpj"