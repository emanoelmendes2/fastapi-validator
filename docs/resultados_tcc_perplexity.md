# TEXTO COMPLETO DOS RESULTADOS PARA O PERPLEXITY MONTAR A SEÇÃO DE RESULTADOS DO TCC

Contexto: Este é o capítulo de Resultados de um TCC sobre uma ferramenta chamada FastAPI Validator que analisa APIs RESTful automaticamente. A ferramenta foi descrita na metodologia. Agora precisamos apresentar os resultados da aplicação da ferramenta em duas APIs simuladas. O texto deve ser acadêmico, formal, em português brasileiro, sem emojis. As figuras e tabelas são referenciadas no texto mas serão inseridas depois pelo autor. Preciso que você monte o texto completo seguindo exatamente a estrutura abaixo, usando todos os dados fornecidos.

---

## ESTRUTURA DO CAPÍTULO DE RESULTADOS

### Seção 1 — Desenvolvimento da ferramenta de validação

Descrever que a ferramenta foi desenvolvida como biblioteca Python modular com os seguintes componentes: motor de análise (APIAnalyzer), sistema de pontuação (APIScorer), geradores de relatórios (HTMLReporter, CSVReporter, JUnitReporter, GitHubAnnotationsReporter, BadgeGenerator) e interface CLI. O analyzer opera por introspecção em aplicações FastAPI (rotas, modelos Pydantic, metadados), complementado pelo OpenAPIAnalyzer para especificações OpenAPI independentes. Suporta 7 formatos de saída.

Referência visual: "Conforme ilustrado na Figura 1, a arquitetura modular..." (Figura 1 = diagrama de componentes mostrando: CLI → APIAnalyzer/OpenAPIAnalyzer → 33 Regras em 9 Categorias → APIScorer → Reporters → 7 formatos de saída).

### Seção 2 — Categorias e regras de validação

Foram implementadas 33 regras em 9 categorias. Incluir a Tabela 1 com dados:

| Categoria | Peso (%) | Regras | Aspectos validados |
|---|---|---|---|
| Nomenclatura | 10 | 5 | kebab-case, plural, sem verbos, minúsculas, sem trailing slash |
| Métodos HTTP | 15 | 4 | GET sem body, 201 POST, 204 DELETE, body PUT/PATCH |
| Documentação | 10 | 5 | summary, description, tags, operation_id, response_model |
| Status Codes | 10 | 3 | Códigos válidos, responses documentados, erros documentados |
| Response Format | 10 | 2 | snake_case nos campos, Pydantic models |
| Versionamento | 10 | 2 | Versão na URL, consistência entre rotas |
| Segurança | 15 | 4 | Auth em writes, dados sensíveis, HTTPS, deprecated docs |
| Paginação | 10 | 4 | Listas paginadas, consistência, defaults, limite máximo |
| Tratamento Erros | 10 | 4 | Docs de erros, formato consistente, handlers, HTTPException |

Severidades: ERROR (-10 pts), WARNING (-3 pts), INFO (-1 pt). Score base 100 por categoria. Nota final = média ponderada. Grades: A+ (>=95), A (>=85), B (>=70), C (>=55), D (>=40), F (<40).

Referência visual: "A Figura 2 apresenta a saída do comando fastapi-validator rules exibindo as 33 regras..." (Figura 2 = screenshot do terminal com listagem de regras).

### Seção 3 — Aplicação nas APIs simuladas

Duas APIs foram construídas especificamente para validação:

**API A — "API de Gestão Empresarial":** 50 rotas, 8 módulos (produtores, notas fiscais, consultas, documentos, webhooks, clientes, API keys, monitoramento de tasks, health check). Usa autenticação por API Key, paginação em 12 endpoints, modelos Pydantic, 5 métodos HTTP (GET, POST, PUT, PATCH, DELETE). Representa cenário corporativo maduro sem processo formal de validação RESTful.

**API B — "API de Catálogo de Produtos":** 15 rotas, 3 módulos (produtos, categorias, avaliações, health). API em estágio inicial de desenvolvimento com violações moderadas intencionais. Sem autenticação, paginação em 1 endpoint, modelos Pydantic parciais.

Referências visuais:
- "A Figura 3 ilustra a execução do comando fastapi-validator analyze main:app --score na API A..." (Figura 3 = screenshot do terminal colorido mostrando issues agrupados por categoria com score 51.4/100 grade D)
- "A Figura 4 apresenta o relatório HTML gerado para a API A..." (Figura 4 = screenshot do browser mostrando dashboard HTML com grade circle D, barra de score, cards de resumo)

### Seção 4 — Resultados por categoria

Incluir **Tabela 2 — Resultados da API A:**

| Categoria | Nota | Errors | Warnings | Infos | Total Issues |
|---|---|---|---|---|---|
| Nomenclatura | 91 | 0 | 2 | 3 | 5 |
| Métodos HTTP | 64 | 0 | 12 | 0 | 12 |
| Documentação | 0 | 0 | 57 | 54 | 111 |
| Status Codes | 0 | 0 | 50 | 50 | 100 |
| Response Format | 94 | 0 | 0 | 6 | 6 |
| Versionamento | 97 | 0 | 1 | 0 | 1 |
| Paginação | 85 | 0 | 1 | 12 | 13 |
| Segurança | 34 | 0 | 22 | 0 | 22 |
| Tratamento Erros | 0 | 0 | 52 | 0 | 52 |
| **Total** | **51.4 (D)** | **0** | **197** | **125** | **322** |

Incluir **Tabela 3 — Resultados da API B:**

| Categoria | Nota | Errors | Warnings | Infos | Total Issues |
|---|---|---|---|---|---|
| Nomenclatura | 78 | 0 | 7 | 1 | 8 |
| Métodos HTTP | 91 | 0 | 3 | 0 | 3 |
| Documentação | 0 | 0 | 22 | 34 | 56 |
| Status Codes | 40 | 0 | 15 | 15 | 30 |
| Response Format | 100 | 0 | 0 | 0 | 0 |
| Versionamento | 97 | 0 | 1 | 0 | 1 |
| Paginação | 99 | 0 | 0 | 1 | 1 |
| Segurança | 72 | 1 | 6 | 0 | 7 |
| Tratamento Erros | 37 | 0 | 21 | 0 | 21 |
| **Total** | **69.5 (C)** | **1** | **75** | **51** | **127** |

Incluir **Tabela 4 — Exemplos de issues detectados** (1 por categoria, dados reais da API A):

| Categoria | Endpoint | Severidade | Issue detectado | Sugestão gerada |
|---|---|---|---|---|
| Nomenclatura | GET /notas-fiscais/download/xml/{uuid} | WARNING | URL contém o verbo 'download' | Usar GET /recursos/{id}/arquivo |
| Métodos HTTP | POST /produtores/{uuid}/ativar | WARNING | POST retorna 200, deveria ser 201 | Adicionar status_code=201 ao decorator |
| Documentação | POST /produtores | WARNING | Endpoint não tem summary | Adicionar parâmetro summary= ao decorator |
| Status Codes | POST /produtores | WARNING | Sem responses adicionais documentados | Adicionar responses={...} para erros comuns |
| Response Format | GET /documento-distribuido/chave/{chave} | INFO | Response model não é tipo válido | Usar modelo Pydantic como response_model |
| Versionamento | (toda a API) | WARNING | API não possui versionamento na URL | Adicionar prefixo /v1/ |
| Segurança | POST /produtores | WARNING | Endpoint que modifica dados sem auth | Adicionar dependência de autenticação |
| Paginação | GET /admin/clientes | WARNING | Lista sem parâmetros de paginação | Adicionar parâmetros page, limit |
| Tratamento Erros | POST /produtores | WARNING | Não documenta respostas de erro 4xx/5xx | Adicionar responses com códigos de erro |

Referências visuais:
- "A Figura 5 apresenta gráfico comparativo das notas por categoria entre as duas APIs" (Figura 5 = gráfico de barras agrupadas, 9 categorias, 2 barras por categoria — API A azul, API B laranja)
- "A Figura 6 exibe a distribuição percentual dos issues por categoria na API A" (Figura 6 = gráfico de pizza: Documentação 34.5%, Status Codes 31.1%, Tratamento Erros 16.1%, Segurança 6.8%, Paginação 4.0%, Métodos HTTP 3.7%, Response 1.9%, Nomenclatura 1.6%, Versionamento 0.3%)

### Seção 5 — Análise quantitativa

Incluir **Tabela 5 — Métricas de execução comparativas:**

| Métrica | API A | API B |
|---|---|---|
| Rotas analisadas | 50 | 15 |
| Regras executadas | 33 | 33 |
| Regras aprovadas (sem issues) | 17 | 15 |
| Regras com issues | 16 | 18 |
| Tempo de execução | 32.04 ms | 7.78 ms |
| Total de issues | 322 | 127 |
| Issues por rota (média) | 6.44 | 8.47 |
| Cobertura de categorias sem issues | 0% | 11.11% |

Discussão a incluir no texto: A API B tem score superior (69.5 vs 51.4) mas maior densidade de issues por rota (8.47 vs 6.44), indicando que APIs menores não são necessariamente mais conformes. A API A zerou em 3 categorias (documentação, status codes, tratamento de erros) enquanto a API B zerou em 1 (documentação), revelando que documentação é o ponto mais negligenciado em ambos os cenários. O tempo de execução (32ms e 7.78ms) contrasta com estimativa de 4 a 6 horas para revisão manual equivalente de 50 rotas, representando redução superior a 99.99% no tempo de validação. A estimativa manual foi baseada em tempo médio de 5 a 7 minutos por endpoint para verificar manualmente as 33 regras (nomenclatura, HTTP, docs, status, response, versioning, security, pagination, error handling).

### Seção 6 — Análise qualitativa

Na API A, 81.7% dos issues (263 de 322) concentraram-se em documentação (111), status codes (100) e tratamento de erros (52). Na API B, 84.3% dos issues (107 de 127) concentraram-se nas mesmas 3 categorias: documentação (56), status codes (30) e tratamento de erros (21). Este padrão consistente sugere que a documentação formal de endpoints e respostas de erro é sistematicamente negligenciada no desenvolvimento de APIs, independentemente da maturidade do projeto.

As categorias com melhor desempenho em ambas as APIs foram response format (94 e 100), versionamento (97 e 97) e nomenclatura (91 e 78). Isso sugere que o framework FastAPI, combinado com Pydantic, já induz boas práticas nessas áreas por padrão — a tipagem e os modelos Pydantic garantem respostas bem estruturadas, enquanto as convenções de nomenclatura do Python favorecem snake_case naturalmente.

A segurança apresentou divergência significativa: API A (34) vs API B (72). A API A, apesar de implementar autenticação via API Key, utiliza injeção de dependência através de funções customizadas que a ferramenta não reconheceu como mecanismos de segurança padrão do FastAPI (HTTPBearer, OAuth2), gerando falsos positivos. Este achado é relevante para evolução da ferramenta.

Referência visual: "A Figura 7 apresenta os badges SVG gerados pela ferramenta..." (Figura 7 = 4 badges: API Score 51/100, Grade D, 197 warnings, 0 errors).

### Seção 7 — Integração CI/CD

A ferramenta demonstrou viabilidade para integração em pipelines de CI/CD através dos formatos JUnit XML (compatível com Jenkins, GitLab CI, Azure DevOps, CircleCI), GitHub Actions annotations (renderizadas inline em pull requests) e badges SVG (para documentação em repositórios). O mecanismo quality gate (--fail-under) permite definir score mínimo aceitável; por exemplo, com threshold de 70, a API A (51.4) seria bloqueada automaticamente com exit code 1, enquanto a API B (69.5) também seria bloqueada por margem mínima, demonstrando a aplicabilidade do controle automatizado de qualidade.

Referências visuais:
- "A Figura 8 apresenta o output do formato JUnit XML..." (Figura 8 = screenshot do XML gerado)
- "A Figura 9 demonstra o quality gate bloqueando deploy com --fail-under 70" (Figura 9 = screenshot do terminal mostrando exit code 1)

---

## INSTRUÇÕES PARA O PERPLEXITY

- Montar o texto completo em formato acadêmico formal, português brasileiro
- Usar as referências de figuras e tabelas exatamente como indicado (Figura X, Tabela X)
- Os dados numéricos são reais e devem ser usados exatamente como fornecidos
- Não inventar dados adicionais
- Manter tom analítico e interpretativo nos parágrafos de discussão
- As APIs são chamadas "API A" e "API B" ou pelos nomes descritivos fornecidos
- Não mencionar nomes reais de empresas ou projetos
