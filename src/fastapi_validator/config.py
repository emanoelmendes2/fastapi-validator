"""Carregador de configuração via pyproject.toml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "ValidatorConfig",
    "load_config",
]


@dataclass
class ValidatorConfig:
    """Configuração do fastapi-validator.

    Pode ser definida na seção [tool.fastapi-validator] do pyproject.toml.

    Example:
        [tool.fastapi-validator]
        exclude-rules = ["naming-kebab-case", "docs-operation-id"]
        min-severity = "warning"
        fail-on-warning = false

        [tool.fastapi-validator.category-weights]
        security = 0.25
        naming = 0.05
    """

    exclude_rules: list[str] = field(default_factory=list)
    min_severity: str | None = None
    fail_on_warning: bool = False
    score: bool = False
    output_format: str = "text"
    output_path: str | None = None
    category_weights: dict[str, float] = field(default_factory=dict)
    severity_penalties: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ValidatorConfig:
        """Cria configuração a partir de um dicionário."""
        return cls(
            exclude_rules=data.get("exclude-rules", []),
            min_severity=data.get("min-severity"),
            fail_on_warning=data.get("fail-on-warning", False),
            score=data.get("score", False),
            output_format=data.get("format", "text"),
            output_path=data.get("output"),
            category_weights=data.get("category-weights", {}),
            severity_penalties=data.get("severity-penalties", {}),
        )


def _find_pyproject(start_dir: Path | None = None) -> Path | None:
    """Procura pyproject.toml subindo na árvore de diretórios."""
    current = start_dir or Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / "pyproject.toml"
        if candidate.is_file():
            return candidate
    return None


def _parse_pyproject(path: Path) -> dict[str, Any]:
    """Lê e parseia a seção [tool.fastapi-validator] do pyproject.toml."""
    import sys

    if sys.version_info >= (3, 11):
        import tomllib
    else:
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[no-redef]
            except ImportError:
                return {}

    with open(path, "rb") as f:
        data = tomllib.load(f)

    return data.get("tool", {}).get("fastapi-validator", {})


def load_config(
    config_path: Path | None = None,
    start_dir: Path | None = None,
) -> ValidatorConfig:
    """
    Carrega configuração do pyproject.toml.

    Args:
        config_path: Caminho direto para pyproject.toml (opcional)
        start_dir: Diretório inicial para busca (opcional)

    Returns:
        Configuração carregada ou defaults se não encontrar arquivo
    """
    path = config_path or _find_pyproject(start_dir)
    if path is None:
        return ValidatorConfig()

    data = _parse_pyproject(path)
    if not data:
        return ValidatorConfig()

    return ValidatorConfig.from_dict(data)
