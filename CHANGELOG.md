# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

## [0.1.0] - 2026-02-08

### Adicionado

- **Validadores** de campo: `StringValidator`, `NumberValidator`, `EmailValidator`, `CPFValidator`, `CNPJValidator`
- **Decorators** `@validate_request` e `@validate_response` para validação inline
- **Middleware** `ValidationMiddleware` para tratamento global de erros de validação
- **Analisador de API** com 8 categorias de regras (naming, http, docs, status, response, versioning, security, pagination)
- **Sistema de scoring** com grades A+ a F e pesos configuráveis por categoria
- **Detector de breaking changes** entre versões de API
- **Analisador de dependências** com detecção de segurança e dependências circulares
- **Auto-fix** com sugestões de código para correção de issues
- **Relatórios** em múltiplos formatos: HTML, JSON, JUnit XML, GitHub Actions, Badges SVG
- **CLI** `fastapi-validator` com comandos `analyze` e `rules`
- Suporte para Python 3.9, 3.10, 3.11, 3.12
- Suporte a configuração via `pyproject.toml` (`[tool.fastapi-validator]`)
- Pre-commit hooks com ruff e mypy
- Marcador `py.typed` para PEP 561
