"""Testes para as regras de métodos HTTP."""

import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_validator.analyzer.rules.http_methods import (
    DeleteStatusRule,
    GetNoBodyRule,
    PostStatusRule,
    PutPatchBodyRule,
)


class UserCreate(BaseModel):
    name: str
    email: str


class TestGetNoBodyRule:
    """Testes para GetNoBodyRule."""

    def test_get_without_body_ok(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def get_users():
            return []

        rule = GetNoBodyRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_get_with_body_detected(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def get_users(body: UserCreate):
            return []

        rule = GetNoBodyRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("body" in i.message.lower() for i in issues)


class TestPostStatusRule:
    """Testes para PostStatusRule."""

    def test_post_201_ok(self) -> None:
        app = FastAPI()

        @app.post("/users", status_code=201)
        async def create_user():
            return {}

        rule = PostStatusRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_post_200_warning(self) -> None:
        app = FastAPI()

        @app.post("/users")
        async def create_user():
            return {}

        rule = PostStatusRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("201" in i.message for i in issues)

    def test_post_login_ok(self) -> None:
        app = FastAPI()

        @app.post("/login")
        async def login():
            return {"token": "abc"}

        rule = PostStatusRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_post_auth_ok(self) -> None:
        app = FastAPI()

        @app.post("/auth/token")
        async def get_token():
            return {"token": "abc"}

        rule = PostStatusRule()
        issues = rule.check(app)

        assert len(issues) == 0


class TestDeleteStatusRule:
    """Testes para DeleteStatusRule."""

    def test_delete_204_ok(self) -> None:
        app = FastAPI()

        @app.delete("/users/{id}", status_code=204)
        async def delete_user(id: int):
            pass

        rule = DeleteStatusRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_delete_200_warning(self) -> None:
        app = FastAPI()

        @app.delete("/users/{id}", status_code=200)
        async def delete_user(id: int):
            return {"deleted": True}

        rule = DeleteStatusRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("204" in i.message for i in issues)


class TestPutPatchBodyRule:
    """Testes para PutPatchBodyRule."""

    def test_put_with_body_ok(self) -> None:
        app = FastAPI()

        @app.put("/users/{id}")
        async def update_user(id: int, user: UserCreate):
            return {"id": id, **user.model_dump()}

        rule = PutPatchBodyRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_put_without_body_warning(self) -> None:
        app = FastAPI()

        @app.put("/users/{id}")
        async def update_user(id: int):
            return {"id": id}

        rule = PutPatchBodyRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("body" in i.message.lower() for i in issues)

    def test_patch_with_body_ok(self) -> None:
        app = FastAPI()

        @app.patch("/users/{id}")
        async def partial_update_user(id: int, user: UserCreate):
            return {"id": id}

        rule = PutPatchBodyRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_patch_without_body_warning(self) -> None:
        app = FastAPI()

        @app.patch("/users/{id}")
        async def partial_update_user(id: int):
            return {"id": id}

        rule = PutPatchBodyRule()
        issues = rule.check(app)

        assert len(issues) > 0