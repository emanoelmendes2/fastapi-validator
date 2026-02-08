"""Testes para as regras de documentação."""

import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_validator.analyzer.rules.documentation import (
    DescriptionRequiredRule,
    OperationIdRule,
    ResponseModelRule,
    SummaryRequiredRule,
    TagsRequiredRule,
)


class UserResponse(BaseModel):
    id: int
    name: str


class TestSummaryRequiredRule:
    """Testes para SummaryRequiredRule."""

    def test_with_summary_ok(self) -> None:
        app = FastAPI()

        @app.get("/users", summary="List all users")
        async def get_users():
            return []

        rule = SummaryRequiredRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_without_summary_warning(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def get_users():
            return []

        rule = SummaryRequiredRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("summary" in i.message.lower() for i in issues)


class TestDescriptionRequiredRule:
    """Testes para DescriptionRequiredRule."""

    def test_with_docstring_ok(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def get_users():
            """Get all users from the database."""
            return []

        rule = DescriptionRequiredRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_with_description_param_ok(self) -> None:
        app = FastAPI()

        @app.get("/users", description="Get all users from the database")
        async def get_users():
            return []

        rule = DescriptionRequiredRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_without_description_info(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def get_users():
            return []

        rule = DescriptionRequiredRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("description" in i.message.lower() for i in issues)


class TestTagsRequiredRule:
    """Testes para TagsRequiredRule."""

    def test_with_tags_ok(self) -> None:
        app = FastAPI()

        @app.get("/users", tags=["users"])
        async def get_users():
            return []

        rule = TagsRequiredRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_without_tags_info(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def get_users():
            return []

        rule = TagsRequiredRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("tags" in i.message.lower() for i in issues)


class TestOperationIdRule:
    """Testes para OperationIdRule."""

    def test_with_operation_id_ok(self) -> None:
        app = FastAPI()

        @app.get("/users", operation_id="listUsers")
        async def get_users():
            return []

        rule = OperationIdRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_without_operation_id_info(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def get_users():
            return []

        rule = OperationIdRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("operation_id" in i.message.lower() for i in issues)


class TestResponseModelRule:
    """Testes para ResponseModelRule."""

    def test_with_response_model_ok(self) -> None:
        app = FastAPI()

        @app.get("/users", response_model=list[UserResponse])
        async def get_users():
            return []

        rule = ResponseModelRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_without_response_model_warning(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def get_users():
            return []

        rule = ResponseModelRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("response_model" in i.message.lower() for i in issues)

    def test_delete_without_response_model_ok(self) -> None:
        app = FastAPI()

        @app.delete("/users/{id}")
        async def delete_user(id: int):
            pass

        rule = ResponseModelRule()
        issues = rule.check(app)

        assert len(issues) == 0
