"""Testes para as regras de nomenclatura."""

import pytest
from fastapi import FastAPI

from fastapi_validator.analyzer.rules.naming import (
    KebabCaseRule,
    LowercaseRule,
    NoTrailingSlashRule,
    NoVerbsRule,
    PluralResourcesRule,
)


class TestKebabCaseRule:
    """Testes para KebabCaseRule."""

    def test_valid_kebab_case(self) -> None:
        app = FastAPI()

        @app.get("/user-profiles")
        async def get_profiles():
            return []

        rule = KebabCaseRule()
        issues = rule.check(app)

        kebab_issues = [i for i in issues if "user-profiles" in (i.path or "")]
        assert len(kebab_issues) == 0

    def test_underscore_detected(self) -> None:
        app = FastAPI()

        @app.get("/user_profiles")
        async def get_profiles():
            return []

        rule = KebabCaseRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("underscore" in i.message.lower() for i in issues)

    def test_uppercase_detected(self) -> None:
        app = FastAPI()

        @app.get("/userProfiles")
        async def get_profiles():
            return []

        rule = KebabCaseRule()
        issues = rule.check(app)

        assert len(issues) > 0


class TestPluralResourcesRule:
    """Testes para PluralResourcesRule."""

    def test_plural_resource_ok(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def get_users():
            return []

        rule = PluralResourcesRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_singular_resource_detected(self) -> None:
        app = FastAPI()

        @app.get("/user")
        async def get_user():
            return {}

        rule = PluralResourcesRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("singular" in i.message.lower() for i in issues)


class TestNoVerbsRule:
    """Testes para NoVerbsRule."""

    def test_no_verbs_ok(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def list_users():
            return []

        rule = NoVerbsRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_verb_detected(self) -> None:
        app = FastAPI()

        @app.get("/get-users")
        async def get_users():
            return []

        rule = NoVerbsRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("verbo" in i.message.lower() or "verb" in i.message.lower() for i in issues)

    def test_create_verb_detected(self) -> None:
        app = FastAPI()

        @app.post("/create-user")
        async def create_user():
            return {}

        rule = NoVerbsRule()
        issues = rule.check(app)

        assert len(issues) > 0


class TestLowercaseRule:
    """Testes para LowercaseRule."""

    def test_lowercase_ok(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def get_users():
            return []

        rule = LowercaseRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_uppercase_detected(self) -> None:
        app = FastAPI()

        @app.get("/Users")
        async def get_users():
            return []

        rule = LowercaseRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("maiúsculas" in i.message.lower() for i in issues)


class TestNoTrailingSlashRule:
    """Testes para NoTrailingSlashRule."""

    def test_no_trailing_slash_ok(self) -> None:
        app = FastAPI()

        @app.get("/users")
        async def get_users():
            return []

        rule = NoTrailingSlashRule()
        issues = rule.check(app)

        assert len(issues) == 0

    def test_trailing_slash_detected(self) -> None:
        app = FastAPI()

        @app.get("/users/")
        async def get_users():
            return []

        rule = NoTrailingSlashRule()
        issues = rule.check(app)

        assert len(issues) > 0
        assert any("barra" in i.message.lower() for i in issues)

    def test_root_path_ok(self) -> None:
        app = FastAPI()

        @app.get("/")
        async def root():
            return {}

        rule = NoTrailingSlashRule()
        issues = rule.check(app)

        assert len(issues) == 0