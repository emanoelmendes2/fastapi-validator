"""Testes para o analisador de APIs."""

import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_validator import APIAnalyzer, AnalysisReport, Severity


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


class UserCreate(BaseModel):
    name: str
    email: str


def create_test_app() -> FastAPI:
    """Cria uma aplicação de teste."""
    app = FastAPI()

    @app.get("/users", tags=["users"], summary="List users", response_model=list[UserResponse])
    async def list_users():
        """List all users."""
        return []

    @app.post("/users", tags=["users"], summary="Create user", status_code=201, response_model=UserResponse)
    async def create_user(user: UserCreate):
        """Create a new user."""
        return {"id": 1, **user.model_dump()}

    @app.get("/users/{user_id}", tags=["users"], summary="Get user", response_model=UserResponse)
    async def get_user(user_id: int):
        """Get a user by ID."""
        return {"id": user_id, "name": "Test", "email": "test@example.com"}

    @app.delete("/users/{user_id}", tags=["users"], summary="Delete user", status_code=204)
    async def delete_user(user_id: int):
        """Delete a user."""
        pass

    return app


def create_bad_app() -> FastAPI:
    """Cria uma aplicação com problemas."""
    app = FastAPI()

    @app.get("/GetUser/{userId}")
    async def get_user(userId: int):
        return {"id": userId}

    @app.post("/create_user/")
    async def create_user():
        return {}

    @app.delete("/deleteUser/{id}")
    async def delete_user(id: int):
        return {"deleted": True}

    return app


class TestAPIAnalyzer:
    """Testes para APIAnalyzer."""

    def test_analyze_returns_report(self) -> None:
        app = create_test_app()
        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        assert isinstance(report, AnalysisReport)
        assert report.analyzed_routes > 0

    def test_analyze_good_app_has_fewer_issues(self) -> None:
        good_app = create_test_app()
        bad_app = create_bad_app()

        analyzer = APIAnalyzer()

        good_report = analyzer.analyze(good_app)
        bad_report = analyzer.analyze(bad_app)

        assert len(bad_report.issues) > len(good_report.issues)

    def test_exclude_rules(self) -> None:
        app = create_bad_app()

        analyzer_all = APIAnalyzer()
        analyzer_exclude = APIAnalyzer(exclude_rules=["naming-lowercase", "naming-kebab-case"])

        report_all = analyzer_all.analyze(app)
        report_exclude = analyzer_exclude.analyze(app)

        assert len(report_exclude.issues) < len(report_all.issues)

    def test_min_severity_filter(self) -> None:
        app = create_bad_app()

        analyzer_all = APIAnalyzer()
        analyzer_errors = APIAnalyzer(min_severity=Severity.ERROR)

        report_all = analyzer_all.analyze(app)
        report_errors = analyzer_errors.analyze(app)

        assert len(report_errors.issues) <= len(report_all.issues)
        for issue in report_errors.issues:
            assert issue.severity == Severity.ERROR

    def test_get_available_rules(self) -> None:
        analyzer = APIAnalyzer()
        rules = analyzer.get_available_rules()

        assert len(rules) > 0
        for rule in rules:
            assert "rule_id" in rule
            assert "description" in rule
            assert "severity" in rule


class TestAnalysisReport:
    """Testes para AnalysisReport."""

    def test_error_count(self) -> None:
        app = create_bad_app()
        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        assert report.error_count >= 0
        assert report.error_count == len(report.errors)

    def test_warning_count(self) -> None:
        app = create_bad_app()
        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        assert report.warning_count >= 0
        assert report.warning_count == len(report.warnings)

    def test_info_count(self) -> None:
        app = create_bad_app()
        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        assert report.info_count >= 0
        assert report.info_count == len(report.infos)

    def test_has_errors(self) -> None:
        app = create_bad_app()
        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        assert report.has_errors == (report.error_count > 0)

    def test_to_dict(self) -> None:
        app = create_test_app()
        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)
        result = report.to_dict()

        assert "summary" in result
        assert "issues" in result
        assert "analyzed_routes" in result["summary"]
        assert "total_issues" in result["summary"]
        assert "errors" in result["summary"]
        assert "warnings" in result["summary"]
        assert "infos" in result["summary"]