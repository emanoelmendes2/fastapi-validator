# Contribuindo

Obrigado pelo interesse em contribuir com o **fastapi-validator**!

## Configurando o Ambiente

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/fastapi-validator.git
cd fastapi-validator

# Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instale as dependências de desenvolvimento
pip install -e ".[dev]"

# Instale os pre-commit hooks
pip install pre-commit
pre-commit install
```

## Fluxo de Desenvolvimento

1. Crie uma branch a partir de `main`:
   ```bash
   git checkout -b feature/minha-feature
   ```

2. Faça suas alterações seguindo os padrões do projeto

3. Rode os testes:
   ```bash
   pytest
   ```

4. Rode o linter e type checker:
   ```bash
   ruff check .
   ruff format .
   mypy src/
   ```

5. Faça o commit (os pre-commit hooks rodam automaticamente):
   ```bash
   git commit -m "feat: descrição da mudança"
   ```

6. Abra um Pull Request

## Padrões de Código

- **Formatação**: Ruff (line-length 88, compatível com Black)
- **Linting**: Ruff com regras E, F, W, I, UP, B, C4
- **Types**: mypy em modo strict
- **Python**: Compatível com 3.9+
- **Idioma**: Código em inglês, documentação em português

## Convenção de Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

| Prefixo | Uso |
|---------|-----|
| `feat:` | Nova funcionalidade |
| `fix:` | Correção de bug |
| `docs:` | Documentação |
| `test:` | Testes |
| `refactor:` | Refatoração sem mudança de comportamento |
| `chore:` | Manutenção, dependências, configs |

## Estrutura do Projeto

```
src/fastapi_validator/
├── validators.py        # Validadores de campo
├── decorators.py        # Decorators @validate_request/@validate_response
├── exceptions.py        # Exceções customizadas
├── middleware.py         # Middleware de validação
├── config.py            # Carregador de configuração
├── cli.py               # Interface de linha de comando
├── analyzer/            # Motor de análise de API
│   ├── base.py          # Classes base (Rule, Issue, Severity)
│   ├── runner.py        # Orquestrador principal
│   ├── scoring.py       # Sistema de scoring
│   ├── breaking_changes.py
│   ├── dependencies.py
│   ├── autofix.py
│   └── rules/           # Regras de validação (8 categorias)
└── reports/             # Geradores de relatório
    ├── html.py
    ├── github.py
    ├── junit.py
    └── badges.py
```

## Adicionando Novas Regras

1. Escolha a categoria apropriada em `analyzer/rules/`
2. Crie uma classe que herda de `Rule`:

```python
from fastapi_validator.analyzer.base import Rule, Issue, Severity

class MinhaRegra(Rule):
    rule_id = "categoria-nome"
    description = "Descrição da regra"
    severity = Severity.WARNING

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []
        # Lógica de validação
        return issues
```

3. Registre a regra no `__init__.py` da categoria
4. Adicione testes em `tests/`

## Reportando Bugs

Abra uma issue com:
- Descrição do problema
- Passos para reproduzir
- Comportamento esperado vs atual
- Versão do Python e do fastapi-validator
