# FastAPI Validator

Uma biblioteca completa de validação e análise de qualidade para APIs FastAPI.

## Funcionalidades

- **Validadores de campo** - String, Number, Email, CPF, CNPJ com mensagens customizadas
- **Decorators** - `@validate_request` e `@validate_response` para validação inline
- **Middleware** - Tratamento global de erros de validação
- **Analisador de API** - 8 categorias de regras RESTful (~40 regras)
- **Sistema de scoring** - Grades A+ a F com pesos por categoria
- **Breaking changes** - Detecção de incompatibilidades entre versões
- **Análise de dependências** - Segurança, dependências circulares, sync/async
- **Auto-fix** - Sugestões de código para correção automática
- **Relatórios** - HTML, JSON, JUnit XML, GitHub Actions, Badges SVG
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

O analisador verifica conformidade RESTful em 8 categorias:

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

### Excluindo Regras

```python
analyzer = APIAnalyzer(
    exclude_rules=["naming-kebab-case", "docs-operation-id"],
    min_severity=Severity.WARNING,  # Ignora INFOs
)
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

## CLI

```bash
# Analisar uma aplicação
fastapi-validator analyze myapp:app

# Com score
fastapi-validator analyze myapp:app --score

# Filtrar por severidade
fastapi-validator analyze myapp:app --min-severity warning

# Excluir regras
fastapi-validator analyze myapp:app --exclude naming-kebab-case,docs-operation-id

# Gerar relatório HTML
fastapi-validator analyze myapp:app -f html -o report.html

# Gerar relatório JSON
fastapi-validator analyze myapp:app -f json -o report.json

# Gerar relatório JUnit
fastapi-validator analyze myapp:app -f junit -o results.xml

# Gerar badges
fastapi-validator analyze myapp:app -f badge -o ./badges/

# Listar todas as regras
fastapi-validator rules
```

## Configuração via pyproject.toml

Defina defaults no seu `pyproject.toml`:

```toml
[tool.fastapi-validator]
exclude-rules = ["naming-kebab-case", "docs-operation-id"]
min-severity = "warning"
fail-on-warning = false
score = true

[tool.fastapi-validator.category-weights]
security = 0.25
naming = 0.05
```

As opções de CLI sobrescrevem as configurações do `pyproject.toml`.

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

**Pesos por categoria (default):**

| Categoria | Peso |
|-----------|------|
| Security | 20% |
| HTTP Methods | 15% |
| Documentation | 15% |
| Naming | 10% |
| Status Codes | 10% |
| Response | 10% |
| Versioning | 10% |
| Pagination | 10% |

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
