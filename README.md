# FastAPI Validator

Uma biblioteca completa de validação e análise de qualidade para APIs FastAPI.

## Funcionalidades

- **Validadores de campo** - String, Number, Email, CPF, CNPJ com mensagens customizadas
- **Decorators** - `@validate_request` e `@validate_response` para validação inline
- **Middleware** - Tratamento global de erros de validação
- **Analisador de API** - 9 categorias de regras RESTful (33 regras)
- **Sistema de scoring** - Grades A+ a F com pesos por categoria
- **Quality Gate** - `--fail-under` para CI/CD pipelines
- **Auto-fix** - Sugestões de código para correção automática
- **Baseline** - Salvar e comparar evolução da API ao longo do tempo
- **Breaking changes** - Detecção de incompatibilidades entre versões
- **Análise de dependências** - Segurança, dependências circulares, sync/async
- **Relatórios** - Text, HTML, JSON, JUnit XML, GitHub Actions, Badges SVG, CSV
- **CLI** - Interface de linha de comando completa
- **Configurável** - Via `pyproject.toml`

## Instalação

```bash
pip install fastapi-validator
```

## Uso Rápido

### Validadores de Campo

```python
from fastapi_validator import (
    StringValidator,
    NumberValidator,
    EmailValidator,
    CPFValidator,
    CNPJValidator,
)

# String com limites e padrão regex
string_val = StringValidator(min_length=3, max_length=50, strip=True)
validated = string_val.validate("  hello  ")  # "hello"

# Número com restrições
number_val = NumberValidator(min_value=0, max_value=100, positive_only=True)
validated = number_val.validate(42)

# Email com domínios permitidos
email_val = EmailValidator(allowed_domains=["company.com"])
validated = email_val.validate("user@company.com")

# CPF brasileiro (aceita com ou sem formatação)
cpf_val = CPFValidator()
validated = cpf_val.validate("529.982.247-25")  # "52998224725"

# CNPJ brasileiro (aceita com ou sem formatação)
cnpj_val = CNPJValidator()
validated = cnpj_val.validate("11.222.333/0001-81")  # "11222333000181"
```

### Decorators

```python
from fastapi import FastAPI
from fastapi_validator import validate_request, validate_response, EmailValidator
from pydantic import BaseModel

app = FastAPI()

class UserResponse(BaseModel):
    email: str
    name: str

@app.post("/users")
@validate_request(validators={"email": EmailValidator()})
async def create_user(email: str, name: str):
    return {"email": email, "name": name}

@app.get("/users/{user_id}")
@validate_response(model=UserResponse)
async def get_user(user_id: int):
    return {"email": "user@example.com", "name": "John"}
```

### Middleware

```python
from fastapi import FastAPI
from fastapi_validator import ValidationMiddleware

app = FastAPI()
app.add_middleware(ValidationMiddleware)
# Agora exceções ValidationError são capturadas e retornam JSON formatado
```

## Analisador de API

O analisador verifica conformidade RESTful em 9 categorias:

| Categoria | Exemplos de Regras |
|-----------|-------------------|
| **Naming** | kebab-case, plural, sem verbos, lowercase |
| **HTTP Methods** | GET sem body, POST retorna 201, PUT/PATCH com body |
| **Documentation** | summary, description, tags, response_model |
| **Status Codes** | Códigos válidos, respostas de erro documentadas |
| **Response** | snake_case nos campos, tipagem com Pydantic |
| **Versioning** | Versão na URL (/v1/), consistência entre rotas |
| **Security** | Auth em rotas de escrita, endpoints sensíveis protegidos |
| **Pagination** | Paginação em endpoints de lista, limites definidos |
| **Error Handling** | Respostas de erro documentadas, formato consistente |

### Uso Programático

```python
from fastapi_validator import APIAnalyzer, APIScorer

# Análise
analyzer = APIAnalyzer()
report = analyzer.analyze(app)

print(f"Rotas analisadas: {report.analyzed_routes}")
print(f"Erros: {report.error_count}")
print(f"Warnings: {report.warning_count}")

# Scoring
scorer = APIScorer()
score = scorer.calculate(report)

print(f"Score: {score.total_score}/100 ({score.grade.value})")
```

### Filtrando Regras

```python
from fastapi_validator import APIAnalyzer, Severity

# Excluir regras específicas (blacklist)
analyzer = APIAnalyzer(
    exclude_rules=["naming-kebab-case", "docs-operation-id"],
    min_severity=Severity.WARNING,  # Ignora INFOs
)

# Rodar apenas regras específicas (whitelist)
analyzer = APIAnalyzer(
    include_rules=["naming-kebab-case", "naming-plural-resources", "docs-summary-required"],
)

# Combinar: include filtra primeiro, exclude remove depois
analyzer = APIAnalyzer(
    include_rules=["naming-kebab-case", "naming-plural-resources", "naming-no-verbs"],
    exclude_rules=["naming-no-verbs"],  # Remove naming-no-verbs do whitelist
)
```

## CLI

### Comandos

```bash
# Analisar uma aplicação (auto-descobre app no diretório atual)
fastapi-validator analyze

# Analisar aplicação específica
fastapi-validator analyze myapp:app

# Analisar spec OpenAPI diretamente
fastapi-validator analyze openapi.json
fastapi-validator analyze openapi.yaml

# Listar todas as regras disponíveis
fastapi-validator rules
```

### Opções do comando `analyze`

| Opção | Descrição |
|-------|-----------|
| `APP` | Aplicação no formato `module:app` ou caminho para spec OpenAPI. Se omitido, auto-descobre. |
| `-f, --format FORMAT` | Formato do relatório: `text` (default), `json`, `html`, `junit`, `github`, `badge`, `csv` |
| `-o, --output FILE` | Salvar relatório em arquivo |
| `--score` | Exibir score da API |
| `--min-severity LEVEL` | Severidade mínima: `error`, `warning`, `info` |
| `--exclude RULES` | Regras a excluir, separadas por vírgula |
| `--include RULES` | Rodar apenas estas regras, separadas por vírgula (whitelist) |
| `--no-suggestions` | Não exibir sugestões de correção |
| `--metrics` | Exibir métricas de análise (tempo, cobertura, etc.) |
| `--fail-under SCORE` | Falha se score < valor (quality gate para CI/CD) |
| `--fix` | Exibir sugestões de código para correção automática |
| `--save-baseline FILE` | Salvar resultado como baseline JSON |
| `--baseline FILE` | Comparar com baseline anterior |
| `--no-color` | Desabilitar cores no output |

### Exemplos

```bash
# Análise básica com score
fastapi-validator analyze myapp:app --score

# Filtrar por severidade e excluir regras
fastapi-validator analyze myapp:app --min-severity warning --exclude naming-kebab-case

# Rodar apenas regras de naming e docs
fastapi-validator analyze myapp:app --include naming-kebab-case,naming-plural-resources,docs-summary-required

# Gerar relatório HTML
fastapi-validator analyze myapp:app -f html -o report.html --score

# Gerar relatório JSON
fastapi-validator analyze myapp:app -f json -o report.json

# Gerar relatório JUnit para CI
fastapi-validator analyze myapp:app -f junit -o results.xml

# Gerar badges SVG
fastapi-validator analyze myapp:app -f badge -o ./badges/

# Gerar relatório CSV
fastapi-validator analyze myapp:app -f csv -o report.csv

# Gerar anotações no GitHub Actions
fastapi-validator analyze myapp:app -f github

# Ver métricas de análise
fastapi-validator analyze myapp:app --metrics

# Sugestões de auto-fix
fastapi-validator analyze myapp:app --fix
```

## Quality Gate (CI/CD)

O `--fail-under` permite definir um score mínimo. Se a API não atingir o threshold, o comando retorna exit code 1, falhando o pipeline.

```bash
# Falha se score < 80
fastapi-validator analyze myapp:app --fail-under 80
```

### GitHub Actions

```yaml
name: API Quality
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Instalar dependências
        run: pip install fastapi-validator

      - name: Validar API
        run: fastapi-validator analyze myapp:app --fail-under 80 --score

      - name: Relatório (opcional)
        if: always()
        run: fastapi-validator analyze myapp:app -f github
```

### GitLab CI

```yaml
api-quality:
  script:
    - pip install fastapi-validator
    - fastapi-validator analyze myapp:app --fail-under 80 --score
    - fastapi-validator analyze myapp:app -f junit -o results.xml
  artifacts:
    reports:
      junit: results.xml
```

## Baseline e Evolução

O sistema de baseline permite salvar o estado atual da API e comparar com versões futuras, ideal para acompanhar a evolução da qualidade.

### Fluxo de uso

```bash
# 1. Salvar estado atual como baseline
fastapi-validator analyze myapp:app --save-baseline baseline.json --score

# 2. Fazer modificações na API...

# 3. Comparar com o baseline
fastapi-validator analyze myapp:app --baseline baseline.json --score
```

A comparação mostra:
- Issues novos (regressões)
- Issues resolvidos (melhorias)
- Variação no score
- Variação por categoria

## Regras Disponíveis

### Naming (5 regras)

| Rule ID | Severidade | Descrição |
|---------|------------|-----------|
| `naming-kebab-case` | WARNING | URLs devem usar kebab-case para separar palavras |
| `naming-plural-resources` | WARNING | Recursos devem usar nomes no plural |
| `naming-no-verbs` | WARNING | URLs não devem conter verbos de ação |
| `naming-lowercase` | ERROR | URLs devem ser totalmente em minúsculas |
| `naming-no-trailing-slash` | INFO | URLs não devem terminar com barra |

### HTTP Methods (4 regras)

| Rule ID | Severidade | Descrição |
|---------|------------|-----------|
| `http-get-no-body` | ERROR | Requisições GET não devem ter request body |
| `http-post-status` | WARNING | POST para criação deve retornar status 201 |
| `http-delete-status` | WARNING | DELETE deve retornar status 204 (No Content) |
| `http-put-patch-body` | WARNING | PUT e PATCH devem ter request body |

### Documentation (5 regras)

| Rule ID | Severidade | Descrição |
|---------|------------|-----------|
| `docs-summary-required` | WARNING | Endpoints devem ter summary definido |
| `docs-description-required` | INFO | Endpoints devem ter description definida |
| `docs-tags-required` | INFO | Endpoints devem ter tags para organização |
| `docs-operation-id` | INFO | Endpoints devem ter operation_id definido |
| `docs-response-model` | WARNING | Endpoints devem ter response_model definido |

### Status Codes (3 regras)

| Rule ID | Severidade | Descrição |
|---------|------------|-----------|
| `status-valid-codes` | ERROR | Status codes devem ser códigos HTTP válidos |
| `status-responses-defined` | WARNING | Endpoints devem ter responses documentados |
| `status-error-codes` | INFO | Códigos de erro comuns devem estar documentados |

### Response (2 regras)

| Rule ID | Severidade | Descrição |
|---------|------------|-----------|
| `response-snake-case` | WARNING | Campos de resposta devem usar snake_case |
| `response-pydantic-model` | INFO | Response models devem ser modelos Pydantic |

### Versioning (2 regras)

| Rule ID | Severidade | Descrição |
|---------|------------|-----------|
| `versioning-path` | WARNING | API deve ter versionamento na URL (ex: /v1/) |
| `versioning-consistent` | WARNING | Versionamento deve ser consistente em todas as rotas |

### Security (4 regras)

| Rule ID | Severidade | Descrição |
|---------|------------|-----------|
| `security-auth-required` | WARNING | Endpoints que modificam dados devem ter autenticação |
| `security-sensitive-url` | ERROR | Dados sensíveis não devem estar em parâmetros de URL |
| `security-https` | INFO | API deve usar HTTPS em produção |
| `security-deprecated-docs` | INFO | Endpoints deprecados devem ter documentação de migração |

### Pagination (4 regras)

| Rule ID | Severidade | Descrição |
|---------|------------|-----------|
| `pagination-list-endpoints` | WARNING | Endpoints que retornam listas devem suportar paginação |
| `pagination-consistency` | INFO | Parâmetros de paginação devem ser consistentes |
| `pagination-defaults` | INFO | Parâmetros de paginação devem ter valores padrão |
| `pagination-max-limit` | INFO | Paginação deve ter um limite máximo |

### Error Handling (4 regras)

| Rule ID | Severidade | Descrição |
|---------|------------|-----------|
| `error-response-documented` | WARNING | Endpoints devem documentar respostas de erro (4xx/5xx) |
| `error-consistent-format` | INFO | Respostas de erro devem seguir formato consistente |
| `error-exception-handlers` | INFO | Aplicação deve ter exception handlers registrados |
| `error-http-exception-usage` | WARNING | Endpoints devem usar HTTPException para retornar erros |

**Resumo:** 4 ERROR, 14 WARNING, 15 INFO - Total: 33 regras

## Configuração via pyproject.toml

Defina defaults no seu `pyproject.toml`. As opções de CLI sobrescrevem estas configurações.

### Referência completa

| Opção | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `exclude-rules` | list[str] | `[]` | Regras a desabilitar (blacklist) |
| `include-rules` | list[str] | `[]` | Rodar apenas estas regras (whitelist) |
| `min-severity` | str | `null` | Severidade mínima: `"error"`, `"warning"`, `"info"` |
| `fail-on-warning` | bool | `false` | Falhar quando houver warnings |
| `fail-under` | int | `null` | Score mínimo (quality gate) |
| `score` | bool | `false` | Calcular e exibir score |
| `format` | str | `"text"` | Formato do relatório |
| `output` | str | `null` | Arquivo de saída |

### Exemplo: configuração mínima

```toml
[tool.fastapi-validator]
score = true
```

### Exemplo: CI/CD

```toml
[tool.fastapi-validator]
score = true
fail-under = 80
min-severity = "warning"
exclude-rules = ["docs-description-required", "docs-operation-id"]
```

### Exemplo: apenas regras de segurança e HTTP

```toml
[tool.fastapi-validator]
include-rules = [
    "security-auth-required",
    "security-sensitive-url",
    "security-https",
    "security-deprecated-docs",
    "http-get-no-body",
    "http-post-status",
    "http-delete-status",
    "http-put-patch-body",
]
score = true
fail-under = 90
```

### Exemplo: configuração rigorosa

```toml
[tool.fastapi-validator]
min-severity = "info"
fail-on-warning = true
score = true
fail-under = 85
```

## Configuração Avançada

### Pesos de categorias customizados

Os pesos determinam a importância de cada categoria no cálculo do score. A soma deve ser 1.0.

```toml
[tool.fastapi-validator.category-weights]
naming = 0.05
http = 0.15
docs = 0.10
status = 0.10
response = 0.10
versioning = 0.05
security = 0.25
pagination = 0.10
error_handling = 0.10
```

**Pesos padrão:**

| Categoria | Peso |
|-----------|------|
| Security | 15% |
| HTTP Methods | 15% |
| Naming | 10% |
| Documentation | 10% |
| Status Codes | 10% |
| Response | 10% |
| Versioning | 10% |
| Pagination | 10% |
| Error Handling | 10% |

### Penalidades por severidade customizadas

Controla quanto cada tipo de issue reduz o score da categoria.

```toml
[tool.fastapi-validator.severity-penalties]
error = 15.0
warning = 5.0
info = 1.0
```

**Penalidades padrão:** ERROR = 10.0, WARNING = 3.0, INFO = 1.0

### Combinando include e exclude

Quando ambos são definidos, `include` é aplicado primeiro (whitelist), e `exclude` remove regras do resultado:

```toml
[tool.fastapi-validator]
# Começa com todas as regras de naming
include-rules = [
    "naming-kebab-case",
    "naming-plural-resources",
    "naming-no-verbs",
    "naming-lowercase",
    "naming-no-trailing-slash",
]
# Remove uma específica
exclude-rules = ["naming-no-trailing-slash"]
```

Equivalente no CLI:

```bash
fastapi-validator analyze myapp:app \
    --include naming-kebab-case,naming-plural-resources,naming-no-verbs,naming-lowercase,naming-no-trailing-slash \
    --exclude naming-no-trailing-slash
```

## Breaking Changes

Detecta incompatibilidades entre duas versões da API:

```python
from fastapi_validator import BreakingChangesDetector

detector = BreakingChangesDetector()
report = detector.compare(old_app, new_app)

if report.has_breaking_changes:
    print("Breaking changes detectadas!")
    for change in report.breaking_changes:
        print(f"  - {change.description}")
```

Detecta: remoção de endpoints/parâmetros, mudança de tipos, remoção de campos de resposta, mudança de status codes.

## Análise de Dependências

```python
from fastapi_validator import DependencyAnalyzer

dep_analyzer = DependencyAnalyzer()
report = dep_analyzer.analyze(app)

print(f"Cobertura de segurança: {report.security_coverage:.1f}%")
for issue in report.issues:
    print(f"  - {issue.message}")
```

## Auto-fix

Gera sugestões de código para correção:

```python
from fastapi_validator import APIAnalyzer, AutoFixer

analyzer = APIAnalyzer()
report = analyzer.analyze(app)

fixer = AutoFixer()
suggestions = fixer.generate_suggestions(app, report.issues)

for s in suggestions.suggestions:
    print(f"[{s.issue.rule_id}] {s.explanation}")
    if s.can_auto_fix:
        print(f"  Antes: {s.original_code}")
        print(f"  Depois: {s.suggested_code}")
```

## Relatórios

### HTML

```python
from fastapi_validator.reports import HTMLReporter

reporter = HTMLReporter()
reporter.save(report, "report.html", score, app_title="Minha API")
```

### JUnit XML (CI/CD)

```python
from fastapi_validator.reports import JUnitReporter

junit = JUnitReporter()
junit.save(report, "test-results.xml")
```

### GitHub Actions

```python
from fastapi_validator.reports import GitHubAnnotationsReporter

github = GitHubAnnotationsReporter()
print(github.generate(report))  # Gera anotações inline no PR
```

### Badges SVG

```python
from fastapi_validator.reports import BadgeGenerator

badges = BadgeGenerator()
badges.save_all_badges(score, "./badges/", error_count=report.error_count)
```

## Validadores Disponíveis

| Validador | Parâmetros | Descrição |
|-----------|-----------|-----------|
| `StringValidator` | `min_length`, `max_length`, `pattern`, `strip`, `lowercase`, `uppercase` | Valida strings |
| `NumberValidator` | `min_value`, `max_value`, `allow_float`, `positive_only` | Valida números |
| `EmailValidator` | `allowed_domains` | Valida emails |
| `CPFValidator` | - | Valida CPF brasileiro |
| `CNPJValidator` | - | Valida CNPJ brasileiro |

## Sistema de Scoring

| Grade | Score | Descrição |
|-------|-------|-----------|
| A+ | >= 95 | Excelente |
| A | >= 85 | Muito bom |
| B | >= 70 | Bom |
| C | >= 55 | Regular |
| D | >= 40 | Fraco |
| F | < 40 | Crítico |

## Desenvolvimento

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/fastapi-validator.git
cd fastapi-validator

# Instale com dependências de dev
pip install -e ".[dev]"

# Instale pre-commit hooks
pip install pre-commit
pre-commit install

# Rode testes
pytest

# Linting e formatação
ruff check .
ruff format .

# Type checking
mypy src/
```

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes.

## Licença

MIT
