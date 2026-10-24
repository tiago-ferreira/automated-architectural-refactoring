# Refatoração Arquitetural Automatizada com Agent Skills (`refactor-arch`)

Este repositório contém a solução completa do desafio técnico de **Refatoração Arquitetural Automatizada**, incluindo a análise manual de 3 sistemas legados (Python/Flask e Node.js/Express), a criação da Skill agêntica agnóstica de tecnologia `refactor-arch` (estruturada em 3 fases sequenciais), os relatórios de auditoria gerados (`reports/audit-project-{1,2,3}.md`) e o código-fonte dos 3 projetos refatorados para o padrão **MVC (Model-View-Controller)**.

---

## Sumário

1. [Análise Manual](#1-análise-manual)
2. [Construção da Skill](#2-construção-da-skill)
3. [Resultados](#3-resultados)
4. [Como Executar](#4-como-executar)

---

## 1. Análise Manual

Antes de projetar a skill `refactor-arch`, os 3 projetos legados foram inspecionados manualmente para mapear vulnerabilidades de segurança, violações de arquitetura MVC/SOLID e problemas de performance/qualidade.

### 1.1 Projeto 1 — `code-smells-project/` (Python/Flask — API de E-commerce)

API monolítica em 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`) sem separação real por domínio, repleta de falhas críticas de segurança e acoplamento.

| # | Severidade | Problema / Anti-Pattern | Arquivo e Linhas | Justificativa e Impacto Arquitetural |
|---|---|---|---|---|
| 1 | **CRITICAL** | **SQL Injection Generalizado & Execução Arbitrária de SQL** | `models.py:28`, `models.py:47-50`, `models.py:57-61`, `models.py:68`, `models.py:92`, `models.py:109-111`, `models.py:126-129`, `models.py:140-166`, `models.py:279-281`, `models.py:289-299` e `app.py:59-79` | Todas as queries concatenam strings diretamente (`"SELECT * FROM usuarios WHERE email = '" + email + "'..."`), permitindo bypass de autenticação e perda total de dados. Além disso, a rota `/admin/query` (`app.py:59-79`) executa qualquer SQL enviado no payload sem autenticação. |
| 2 | **CRITICAL** | **Hardcoded Credentials & Exposição de Segredo em Endpoint** | `app.py:7-8`, `database.py:75-79` e `controllers.py:288-289` | A `SECRET_KEY` (`"minha-chave-super-secreta-123"`) está hardcoded no código-fonte e, pior ainda, é exposta publicamente no retorno JSON do endpoint `/health` (`controllers.py:289`), comprometendo toda a segurança criptográfica da aplicação. Senhas de usuários também são salvas e retornadas em texto puro (`models.py:83, 99, 127`). |
| 3 | **CRITICAL** | **God Module / Violação Severa de SRP** | `models.py:1-314` e `controllers.py:1-292` | `models.py` concentra acesso a dados, regras de negócio (cálculo de pedidos, estoque e descontos de relatório) e formatação de 4 domínios (`produtos`, `usuarios`, `pedidos`, `relatorios`) em funções procedurais globais. Analogamente, `controllers.py` mistura roteamento/HTTP, validação, queries diretas ao banco (`controllers.py:266-274`) e simulação de envio de email/SMS/push (`controllers.py:208-210`). |
| 4 | **HIGH** | **Estado Global Mutável e Conexão SQLite Compartilhada entre Threads** | `database.py:4-10` | Uso de variável global `db_connection` inicializada com `sqlite3.connect(db_path, check_same_thread=False)` compartilhada por todas as requisições sem controle de ciclo de vida por request (`flask.g`), causando condições de corrida (race conditions) e corrupção de transações sob concorrência. |
| 5 | **MEDIUM** | **Queries N+1 Aninhadas (Gargalo de Performance)** | `models.py:139-166`, `models.py:177-200` e `models.py:209-232` | Em `get_pedidos_usuario` e `get_todos_pedidos`, para cada pedido é feita 1 query em `itens_pedido` e, dentro de outro loop, 1 query em `produtos` para buscar o nome (`1 + N + (N*M)` queries), degradando drasticamente a latência conforme o banco cresce. |
| 6 | **MEDIUM** | **Ausência de Error Handling Centralizado e Duplicação Massiva** | `controllers.py:5-292` e `models.py:171-233` | Todos os 14 handlers em `controllers.py` repetem blocos `try ... except Exception as e: return jsonify({"erro": str(e)}), 500`, vazando detalhes internos de exceções ao cliente. Há ainda duplicação quase idêntica entre `get_pedidos_usuario` e `get_todos_pedidos` em `models.py`. |
| 7 | **LOW** | **Magic Numbers em Regras de Desconto e Categorias Hardcoded** | `models.py:257-262` e `controllers.py:47-53` | Faixas de faturamento (`10000`, `5000`, `1000`) e percentuais (`0.1`, `0.05`, `0.02`) estão soltos em `relatorio_vendas()`, assim como limites de tamanho (`2`, `200`) e lista de categorias válidas hardcoded dentro do controller. |
| 8 | **LOW** | **Uso de `print()` para Logging e Formatação Manual com `+`** | `app.py:56, 83-86` e `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250` | Uso de `print()` concatenando strings com `+` em vez do módulo estruturado `logging`, poluindo stdout sem níveis de severidade ou timestamps. |

### 1.2 Projeto 2 — `ecommerce-api-legacy/` (Node.js/Express — LMS API com Checkout)

Aplicação Node.js/Express centrada em uma única classe monolítica (`AppManager.js`) que gerencia banco SQLite em memória, rotas, regras de checkout e relatórios financeiros.

| # | Severidade | Problema / Anti-Pattern | Arquivo e Linhas | Justificativa e Impacto Arquitetural |
|---|---|---|---|---|
| 1 | **CRITICAL** | **God Class (`AppManager`) / Ausência Total de Camadas MVC** | `src/AppManager.js:4-139` | A classe `AppManager` instancia o banco de dados, cria tabelas, faz seed de dados, define todas as rotas Express (`setupRoutes`), executa regras de pagamento, matrícula, auditoria e agregação financeira no mesmo arquivo, violando completamente o SRP e o padrão MVC. |
| 2 | **CRITICAL** | **Hardcoded Credentials, Vazamento de PCI/Segredos em Logs e Criptografia Insegura** | `src/utils.js:1-7`, `src/utils.js:17-23` e `src/AppManager.js:18, 45, 68` | Credenciais críticas (`dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`) estão hardcoded em `src/utils.js:2-4`. Em `src/AppManager.js:45`, o número completo do cartão de crédito (`cc`) e a chave privada do gateway são impressos no `console.log`. Além disso, `badCrypto` (`src/utils.js:17-23`) apenas repete os 2 primeiros caracteres do Base64 da senha num loop inútil de 10.000 iterações (bloqueando o Event Loop e gerando pseudo-hash reversível/colidente). |
| 3 | **HIGH** | **Callback Hell, Forte Acoplamento e Violação de Integridade Transacional** | `src/AppManager.js:28-78` e `src/AppManager.js:131-137` | O fluxo de `/api/checkout` encadeia até 6 níveis de callbacks aninhados misturando `this.db` e `self.db` sem transação SQL (`BEGIN`/`COMMIT`/`ROLLBACK`). Na rota `DELETE /api/users/:id` (`src/AppManager.js:131-137`), o usuário é removido sem limpar ou tratar `enrollments` e `payments` associados, deixando registros órfãos no banco. |
| 4 | **HIGH** | **Estado Global Mutável sem Limite (`globalCache` / `totalRevenue`)** | `src/utils.js:9-15` e `src/AppManager.js:2, 59` | `globalCache` armazena dados de negócio em memória global via `logAndCache` (função que mistura duas responsabilidades: logging e cache) sem política de expiração (memory leak), enquanto `totalRevenue` é exportado como estado global mutável. |
| 5 | **MEDIUM** | **Problema de Query N+1 Severo no Relatório Financeiro** | `src/AppManager.js:80-129` | A rota `GET /api/admin/financial-report` faz `SELECT * FROM courses`, depois `SELECT * FROM enrollments` para cada curso e, para cada matrícula, dispara mais 2 queries (`SELECT ... FROM users` e `SELECT ... FROM payments`), controlando a sincronização assíncrona manualmente com contadores (`coursesPending`, `enrPending`) sujeitos a race conditions quando há erro de DB. |
| 6 | **MEDIUM** | **Ausência de Middleware Centralizado de Erros e Validações Frágeis** | `src/app.js:1-14` e `src/AppManager.js:35, 38, 41, 51, 55, 70, 84, 133` | Não há middleware global de tratamento de erros no Express (`app.use((err, req, res, next) => ...)`). Erros de SQL em `financial-report` (linhas 92, 104, 106) e `DELETE /api/users/:id` (linha 133) são ignorados silenciosamente, podendo travar a requisição sem resposta (`coursesPending` nunca chega a zero). |
| 7 | **LOW** | **Nomenclatura Críptica de Variáveis e Parâmetros** | `src/AppManager.js:29-33, 52, 89, 102` | Uso de variáveis de 1 a 3 letras (`u`, `e`, `p`, `cid`, `cc`, `c`, `enr`, `enrId`) que prejudicam a legibilidade e manutenção do domínio de checkout e matrículas. |
| 8 | **LOW** | **Magic Numbers e Strings de Regra de Negócio Hardcoded** | `src/utils.js:6, 19-22` e `src/AppManager.js:46, 68` | Porta `3000`, contagens mágicas `10000`, `2`, `10` em `badCrypto`, senha default `"123456"` e regra de aprovação de cartão `cc.startsWith("4")` espalhados diretamente na lógica de rota. |

### 1.3 Projeto 3 — `task-manager-api/` (Python/Flask — API de Task Manager)

Projeto parcialmente organizado em pastas (`models/`, `routes/`, `services/`, `utils/`), mas **sem camada de Controllers** (toda a lógica de negócio, persistência e agregação reside diretamente nos arquivos de rotas), além de conter falhas críticas de segurança, queries N+1 e uso extensivo de APIs deprecated.

| # | Severidade | Problema / Anti-Pattern | Arquivo e Linhas | Justificativa e Impacto Arquitetural |
|---|---|---|---|---|
| 1 | **CRITICAL** | **Hardcoded Credentials, Hash MD5 sem Salt, Vazamento de Hash em JSON e Fake JWT** | `app.py:13`, `services/notification_service.py:7-10`, `models/user.py:21, 29, 32` e `routes/user_routes.py:210` | `SECRET_KEY = 'super-secret-key-123'` (`app.py:13`) e credenciais SMTP (`email_password = 'senha123'` em `services/notification_service.py:10`) estão hardcoded. `User` usa MD5 puro (`hashlib.md5`) para senhas (`models/user.py:29, 32`), expõe o campo `'password'` em `User.to_dict()` (`models/user.py:21` — vazado em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`), e retorna um token falso previsível `'fake-jwt-token-' + str(user.id)` (`routes/user_routes.py:210`). |
| 2 | **HIGH** | **Fat Routes / Ausência da Camada de Controllers (Violação do Padrão MVC)** | `routes/task_routes.py:11-299`, `routes/user_routes.py:10-211` e `routes/report_routes.py:12-223` | Embora existam diretórios `routes/` e `models/`, não há camada `controllers/`. As rotas manipulam diretamente `db.session.add/commit/rollback`, executam dezenas de queries e cálculos estatísticos em memória (`summary_report`, `user_report`, `task_stats`) e misturam o CRUD de `categories` dentro de `routes/report_routes.py:157-223` (violação de coesão/SRP). Além disso, métodos dos models (`Task.validate_status`, `Task.validate_priority`, `Task.is_overdue`) e helpers (`utils/helpers.py:process_task_data`) são ignorados e reimplementados inline nas rotas. |
| 3 | **MEDIUM** | **Uso de APIs Deprecated do SQLAlchemy 2.0 (`Query.get`) e Python 3.12+ (`datetime.utcnow`)** | `routes/task_routes.py:31, 42, 51, 67, 72, 117, 122, 158, 188, 195, 215, 227, 285`, `routes/user_routes.py:29, 94, 136, 155, 172`, `routes/report_routes.py:35, 42, 45, 71, 105, 133, 192, 213` e `models/task.py:15-16, 52` | Uso de `Model.query.get(id)` (depreciado no SQLAlchemy 2.0 em favor de `db.session.get(Model, id)`) em 15 pontos das rotas, e uso de `datetime.utcnow()` (depreciado no Python 3.12+ em favor de `datetime.now(timezone.utc)`) em mais de 20 locais nos models, routes, services, utils e seed. |
| 4 | **MEDIUM** | **Queries N+1 e Agregações Ineficientes em Memória** | `routes/task_routes.py:14-59, 275-288`, `routes/user_routes.py:12-24` e `routes/report_routes.py:15-68, 159-164` | Em `GET /tasks` (`task_routes.py:42, 51`), para cada task são disparadas até 2 queries extras (`User.query.get` e `Category.query.get`). Em `GET /reports/summary` (`report_routes.py:53-68`) e `GET /categories` (`report_routes.py:163`), executa-se 1 query adicional por usuário/categoria dentro de loops `for`, além de 12 queries `COUNT` separadas para estatísticas de status e prioridade. |
| 5 | **MEDIUM** | **Bare `except:` e Falta de Error Handler Centralizado** | `routes/task_routes.py:62, 137, 204, 236`, `routes/user_routes.py:130, 149`, `routes/report_routes.py:186, 207, 221` e `utils/helpers.py:46, 49, 88` | Uso de `except:` genérico sem especificar a exceção (capturando inclusive `SystemExit`/`KeyboardInterrupt` e ocultando erros reais) e ausência de `@app.errorhandler` centralizado. Na rota `/tasks/search` (`task_routes.py:261, 264`), `int(priority)` e `int(user_id)` não possuem tratamento, gerando erro 500 se receberem strings não numéricas. |
| 6 | **LOW** | **Imports Não Utilizados, Múltiplos Imports na Mesma Linha e Código Morto** | `app.py:7`, `models/task.py:3`, `routes/task_routes.py:7`, `routes/user_routes.py:5-6`, `routes/report_routes.py:7-8`, `utils/helpers.py:3-7` e `services/notification_service.py:1-48` | Múltiplos imports inutilizados (`import json, os, sys, time`, `import math, hashlib`) que violam a PEP 8, somados a código morto nunca invocado pela aplicação (`NotificationService` inteiro e quase todas as funções/constantes de `utils/helpers.py`). |
| 7 | **LOW** | **Duplicação de Lógica de `overdue`, Checagem `type(x) == list` e Booleans Redundantes** | `models/task.py:38-60`, `models/user.py:34-38`, `routes/task_routes.py:30-40, 71-80, 141, 210, 283-287` e `routes/user_routes.py:171-180` | A lógica de verificação de atraso (`overdue`) é copiada e colada com 3 `if`s aninhados em 6 lugares diferentes em vez de chamar `t.is_overdue()`. Métodos como `is_admin()` e `validate_status()` usam `if cond: return True else: return False`, e checagens de tipo usam `type(tags) == list` em vez de `isinstance(tags, list)`. |

---

## 2. Construção da Skill

### 2.1 Decisões de Design e Anatomia da Skill (`SKILL.md` + `references/`)

A skill `refactor-arch` foi projetada aplicando o princípio de **Progressive Disclosure** (divulgação progressiva de contexto), separando o controle de fluxo e guardrails (`SKILL.md`) do conhecimento profundo de domínio (`references/*.md`). Dessa forma, o agente lê apenas os documentos pertinentes a cada fase, mantendo alta precisão nas regras críticas (como o gate de confirmação da Fase 2 e a preservação de contratos na Fase 3).

```text
.claude/skills/refactor-arch/
├── SKILL.md                                   # Orquestrador das 3 fases e guardrails inegociáveis
└── references/
    ├── 01-project-analysis.md                 # Área 1: Heurísticas de detecção de linguagem, framework, DB e arquitetura
    ├── 02-anti-patterns-catalog.md            # Área 2: Catálogo de 12 anti-patterns (CRITICAL a LOW + APIs deprecated)
    ├── 03-audit-report-template.md            # Área 3: Template padronizado do relatório da Fase 2
    ├── 04-mvc-architecture-guidelines.md      # Área 4: Diretrizes da arquitetura MVC alvo e adaptação estrutural
    └── 05-refactoring-playbook.md             # Área 5: Playbook com 10 transformações práticas (código antes/depois)
```

### 2.2 Catálogo de Anti-Patterns Incluídos e Motivação

O catálogo (`references/02-anti-patterns-catalog.md`) contempla **12 anti-patterns** distribuídos nas quatro severidades exigidas, cobrindo problemas reais de segurança, arquitetura MVC/SOLID, performance e evolução de APIs:

1. **`[CRITICAL]` SQL Injection & Unsanitized Raw Queries**: Detecta concatenação de strings em queries SQL e endpoints que executam SQL arbitrário.
2. **`[CRITICAL]` Hardcoded Credentials & Sensitive Data Exposure**: Detecta chaves secretas, senhas de banco/SMTP e chaves de gateway no código, além de vazamento de segredos/senhas em respostas JSON (`/health`, `to_dict()`) e cartões de crédito em logs.
3. **`[CRITICAL]` God Class / God Module (Monolithic Anti-Pattern)**: Detecta classes ou módulos gigantes (`AppManager.js`, `models.py`, `controllers.py`) que concentram múltiplos domínios, banco de dados, regras de negócio e rotas.
4. **`[CRITICAL]` Broken / Weak Cryptography & Fake Authentication Tokens**: Detecta senhas em texto puro, hashes MD5 sem salt, codificação Base64 disfarçada de criptografia (`badCrypto`) e tokens falsos previsíveis (`fake-jwt-token-<id>`).
5. **`[HIGH]` Fat Routes / Fat Controllers & Missing Controller Layer**: Detecta rotas que acessam diretamente `db.session`/`Model.query`, executam cálculos complexos sem camada de Controller ou misturam domínios distintos (como categorias dentro de rotas de relatórios).
6. **`[HIGH]` Tight Coupling, Callback Hell & Missing Transaction Integrity**: Detecta aninhamento profundo de callbacks assíncronos, ausência de transações atômicas em escritas multi-tabela e deleções que deixam registros órfãos.
7. **`[HIGH]` Mutable Global State & Thread-Unsafe Connections**: Detecta conexões SQLite globais compartilhadas entre threads (`check_same_thread=False`) e caches/acumuladores globais mutáveis (`globalCache`, `totalRevenue`).
8. **`[MEDIUM]` N+1 Query Problem & Inefficient In-Memory Aggregations**: Detecta queries SQL/ORM executadas dentro de loops `for`/`forEach` em listagens e relatórios.
9. **`[MEDIUM]` Deprecated APIs Usage (Obsolete Framework/Language Calls)**: Detecta chamadas obsoletas como `Model.query.get()` (depreciada no SQLAlchemy 2.0 em favor de `db.session.get()`) e `datetime.utcnow()` (depreciada no Python 3.12+ em favor de `datetime.now(timezone.utc)`).
10. **`[MEDIUM]` Missing Centralized Error Handling, Bare `except:` & Duplicated Validation**: Detecta blocos `except:` vazios, ausência de handler global de erros HTTP e callbacks que ignoram erros de banco.
11. **`[LOW]` Magic Numbers, Hardcoded Business Constants & Cryptic Naming**: Detecta variáveis crípticas de 1-2 letras (`u`, `e`, `p`, `cid`, `cc`) e números mágicos soltos em cálculos de desconto e validação.
12. **`[LOW]` Dead Code, Unused/Multiple Imports & Ad-hoc `print`/`console.log`**: Detecta imports inutilizados/múltiplos na mesma linha, serviços/funções órfãs nunca chamadas e expressões booleanas redundantes.

### 2.3 Como o Agnosticismo de Tecnologia foi Garantido

- **Descoberta Baseada em Manifestos e AST/Padrões Léxicos**: Na Fase 1 (`01-project-analysis.md`), a skill identifica a linguagem e o framework inspecionando `requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, etc., sem depender de caminhos hardcoded.
- **Mapeamento Conceitual do MVC para APIs REST**: O guia `04-mvc-architecture-guidelines.md` define contratos de responsabilidade para `Config`, `Models`, `Controllers`, `Views/Routes`, `Middlewares` e `Composition Root` que se traduzem idiomaticamente tanto para Python/Flask (Blueprints + módulos/classes + `flask.g`/SQLAlchemy) quanto para Node.js/Express (Express Router + Classes injetadas + Promises `async/await`).
- **Adaptação Topológica Inteligente**: A skill distingue entre um monolito puro (`code-smells-project`), uma God Class (`ecommerce-api-legacy`) e uma aplicação parcialmente estruturada (`task-manager-api`), preservando o que já está correto e introduzindo apenas as camadas e correções necessárias sem quebrar o entry point (`app.py` ou `src/app.js`).

### 2.4 Desafios Encontrados e Soluções Adotadas

- **Preservação de Contratos HTTP vs. Correção de Falhas de Segurança**: Nos projetos legados, alguns endpoints vazavam dados sensíveis (ex.: `secret_key` em `/health` no Projeto 1 e `password` em `User.to_dict()` no Projeto 3). A solução foi remover exclusivamente os atributos sensíveis vazados e substituir tokens/hashes inseguros por implementações criptográficas reais, mantendo intactos todos os status codes, caminhos de rota e estruturas de dados funcionais.
- **Eliminação de Callbacks Aninhados em SQLite no Node.js**: A biblioteca `sqlite3` no Node.js é baseada em callbacks por padrão. No playbook (`05-refactoring-playbook.md`), criamos um wrapper promisificado (`run`, `get`, `all`) que permitiu reescrever o fluxo de checkout e relatórios usando `async/await`, transações SQL e `LEFT JOIN` sem adicionar dependências externas.
- **Compatibilidade com SQLAlchemy 2.0 e Python 3.12+**: No Projeto 3, a substituição de `datetime.utcnow()` por `datetime.now(timezone.utc)` exigiu normalização (`replace(tzinfo=None)`) ao comparar com colunas `DateTime` ingênuas já gravadas pelo SQLite, evitando `TypeError: can't compare offset-naive and offset-aware datetimes`.

---

## 3. Resultados

### 3.1 Resumo Quantitativo dos Relatórios de Auditoria

Os relatórios completos gerados pela Fase 2 da skill estão salvos em [`reports/audit-project-1.md`](reports/audit-project-1.md), [`reports/audit-project-2.md`](reports/audit-project-2.md) e [`reports/audit-project-3.md`](reports/audit-project-3.md):

| Projeto | Stack Detectada | Arquivos / LOC Analisados | CRITICAL | HIGH | MEDIUM | LOW | Total de Findings | Relatório Completo |
|---|---|---|---:|---:|---:|---:|---:|---|
| **1. `code-smells-project`** | Python + Flask 3.1.1 | 4 arquivos (~778 LOC) | 4 | 3 | 2 | 3 | **12** | [`reports/audit-project-1.md`](reports/audit-project-1.md) |
| **2. `ecommerce-api-legacy`** | Node.js + Express 4.18.2 | 3 arquivos (~180 LOC) | 3 | 3 | 2 | 2 | **10** | [`reports/audit-project-2.md`](reports/audit-project-2.md) |
| **3. `task-manager-api`** | Python + Flask 3.0.0 + SQLAlchemy 3.1.1 | 11 arquivos (~1.153 LOC) | 3 | 2 | 4 | 3 | **12** | [`reports/audit-project-3.md`](reports/audit-project-3.md) |

---

### 3.2 Comparação Antes / Depois da Estrutura de Diretórios

#### Projeto 1 — `code-smells-project/` (Python/Flask)

```text
ANTES (Monolítico — 4 arquivos na raiz)          DEPOIS (Padrão MVC Completo)
code-smells-project/                             code-smells-project/
├── app.py                                       ├── config/
├── controllers.py                               │   ├── __init__.py
├── models.py                                    │   └── settings.py
├── database.py                                  ├── models/
└── requirements.txt                             │   ├── __init__.py
                                                 │   ├── produto_model.py
                                                 │   ├── usuario_model.py
                                                 │   └── pedido_model.py
                                                 ├── controllers/
                                                 │   ├── __init__.py
                                                 │   ├── produto_controller.py
                                                 │   ├── usuario_controller.py
                                                 │   └── pedido_controller.py
                                                 ├── views/
                                                 │   ├── __init__.py
                                                 │   └── routes.py
                                                 ├── middlewares/
                                                 │   ├── __init__.py
                                                 │   └── error_handler.py
                                                 ├── database.py
                                                 ├── app.py (composition root)
                                                 └── requirements.txt
```

#### Projeto 2 — `ecommerce-api-legacy/` (Node.js/Express)

```text
ANTES (God Class em 3 arquivos)                  DEPOIS (Padrão MVC Completo)
ecommerce-api-legacy/                            ecommerce-api-legacy/
├── src/                                         ├── src/
│   ├── app.js                                   │   ├── config/
│   ├── AppManager.js                            │   │   ├── settings.js
│   └── utils.js                                 │   │   └── database.js
├── api.http                                     │   ├── models/
└── package.json                                 │   │   ├── courseModel.js
                                                 │   │   ├── userModel.js
                                                 │   │   ├── enrollmentModel.js
                                                 │   │   └── reportModel.js
                                                 │   ├── controllers/
                                                 │   │   ├── checkoutController.js
                                                 │   │   ├── reportController.js
                                                 │   │   └── userController.js
                                                 │   ├── views/
                                                 │   │   └── routes.js
                                                 │   ├── middlewares/
                                                 │   │   └── errorHandler.js
                                                 │   └── app.js (composition root)
                                                 ├── api.http
                                                 └── package.json
```

#### Projeto 3 — `task-manager-api/` (Python/Flask)

```text
ANTES (Parcialmente organizado, sem Controllers) DEPOIS (Padrão MVC Completo e Desacoplado)
task-manager-api/                                task-manager-api/
├── app.py                                       ├── config/
├── database.py                                  │   ├── __init__.py
├── seed.py                                      │   └── settings.py
├── models/                                      ├── models/
│   ├── task.py                                  │   ├── __init__.py
│   ├── user.py                                  │   ├── task.py
│   └── category.py                              │   ├── user.py
├── routes/                                      │   └── category.py
│   ├── task_routes.py                           ├── controllers/
│   ├── user_routes.py                           │   ├── __init__.py
│   └── report_routes.py (misturava categories)  │   ├── task_controller.py
├── services/                                    │   ├── user_controller.py
│   └── notification_service.py                  │   ├── category_controller.py
└── utils/                                       │   └── report_controller.py
    └── helpers.py                               ├── routes/ (View/Routes HTTP enxutas)
                                                 │   ├── __init__.py
                                                 │   ├── task_routes.py
                                                 │   ├── user_routes.py
                                                 │   ├── category_routes.py
                                                 │   └── report_routes.py
                                                 ├── middlewares/
                                                 │   ├── __init__.py
                                                 │   └── error_handler.py
                                                 ├── services/
                                                 │   └── notification_service.py
                                                 ├── utils/
                                                 │   └── helpers.py
                                                 ├── database.py
                                                 ├── seed.py
                                                 └── app.py (composition root)
```

---

### 3.3 Checklists de Validação Preenchidos (Projetos 1, 2 e 3)

#### Checklist — Projeto 1 (`code-smells-project`)
- **Fase 1 — Análise**
  - [x] Linguagem detectada corretamente (`Python`)
  - [x] Framework detectado corretamente (`Flask 3.1.1`)
  - [x] Domínio da aplicação descrito corretamente (`E-commerce API: produtos, pedidos, itens_pedido, usuarios`)
  - [x] Número de arquivos analisados condiz com a realidade (`4 files analyzed | 778 LOC`)
- **Fase 2 — Auditoria**
  - [x] Relatório segue o template definido nos arquivos de referência (`reports/audit-project-1.md`)
  - [x] Cada finding tem arquivo e linhas exatos
  - [x] Findings ordenados por severidade (`CRITICAL` → `HIGH` → `MEDIUM` → `LOW`)
  - [x] Mínimo de 5 findings identificados (`12 findings`: 4 CRITICAL, 3 HIGH, 2 MEDIUM, 3 LOW)
  - [x] Detecção de APIs deprecated incluída (quando aplicável)
  - [x] Skill pausa e pede confirmação antes da Fase 3 (`Proceed with refactoring (Phase 3)? [y/n]`)
- **Fase 3 — Refatoração**
  - [x] Estrutura de diretórios segue padrão MVC (`config/`, `models/`, `controllers/`, `views/`, `middlewares/`)
  - [x] Configuração extraída para módulo de config (`config/settings.py`, sem hardcoded e sem vazar `secret_key` em `/health`)
  - [x] Models criados para abstrair dados (`produto_model.py`, `usuario_model.py`, `pedido_model.py` com queries 100% parametrizadas)
  - [x] Views/Routes separadas para roteamento (`views/routes.py`)
  - [x] Controllers concentram o fluxo da aplicação (`produto_controller.py`, `usuario_controller.py`, `pedido_controller.py`)
  - [x] Error handling centralizado (`middlewares/error_handler.py`)
  - [x] Entry point claro (`app.py`)
  - [x] Aplicação inicia sem erros
  - [x] Endpoints originais respondem corretamente

#### Checklist — Projeto 2 (`ecommerce-api-legacy`)
- **Fase 1 — Análise**
  - [x] Linguagem detectada corretamente (`JavaScript / Node.js`)
  - [x] Framework detectado corretamente (`Express 4.18.2`)
  - [x] Domínio da aplicação descrito corretamente (`LMS / Course E-commerce API: cursos, matrículas, checkout e relatório financeiro`)
  - [x] Número de arquivos analisados condiz com a realidade (`3 files analyzed | 180 LOC`)
- **Fase 2 — Auditoria**
  - [x] Relatório segue o template definido nos arquivos de referência (`reports/audit-project-2.md`)
  - [x] Cada finding tem arquivo e linhas exatos
  - [x] Findings ordenados por severidade (`CRITICAL` → `HIGH` → `MEDIUM` → `LOW`)
  - [x] Mínimo de 5 findings identificados (`10 findings`: 3 CRITICAL, 3 HIGH, 2 MEDIUM, 2 LOW)
  - [x] Detecção de APIs deprecated incluída (quando aplicável)
  - [x] Skill pausa e pede confirmação antes da Fase 3 (`Proceed with refactoring (Phase 3)? [y/n]`)
- **Fase 3 — Refatoração**
  - [x] Estrutura de diretórios segue padrão MVC (`src/config/`, `src/models/`, `src/controllers/`, `src/views/`, `src/middlewares/`)
  - [x] Configuração extraída para módulo de config (`src/config/settings.js`, cartões mascarados nos logs e `crypto.scryptSync`)
  - [x] Models criados para abstrair dados (`courseModel.js`, `userModel.js`, `enrollmentModel.js`, `reportModel.js`)
  - [x] Views/Routes separadas para roteamento (`src/views/routes.js`)
  - [x] Controllers concentram o fluxo da aplicação (`checkoutController.js`, `reportController.js`, `userController.js`)
  - [x] Error handling centralizado (`src/middlewares/errorHandler.js`)
  - [x] Entry point claro (`src/app.js`)
  - [x] Aplicação inicia sem erros
  - [x] Endpoints originais respondem corretamente

#### Checklist — Projeto 3 (`task-manager-api`)
- **Fase 1 — Análise**
  - [x] Linguagem detectada corretamente (`Python`)
  - [x] Framework detectado corretamente (`Flask 3.0.0 + Flask-SQLAlchemy 3.1.1`)
  - [x] Domínio da aplicação descrito corretamente (`Task Manager API: tarefas, categorias, usuários e relatórios`)
  - [x] Número de arquivos analisados condiz com a realidade (`11 source files analyzed | ~1.153 LOC`)
- **Fase 2 — Auditoria**
  - [x] Relatório segue o template definido nos arquivos de referência (`reports/audit-project-3.md`)
  - [x] Cada finding tem arquivo e linhas exatos
  - [x] Findings ordenados por severidade (`CRITICAL` → `HIGH` → `MEDIUM` → `LOW`)
  - [x] Mínimo de 5 findings identificados (`12 findings`: 3 CRITICAL, 2 HIGH, 4 MEDIUM, 3 LOW)
  - [x] Detecção de APIs deprecated incluída (`Model.query.get()` do SQLAlchemy 2.0 e `datetime.utcnow()` do Python 3.12+)
  - [x] Skill pausa e pede confirmação antes da Fase 3 (`Proceed with refactoring (Phase 3)? [y/n]`)
- **Fase 3 — Refatoração**
  - [x] Estrutura de diretórios segue padrão MVC (`config/`, `models/`, `controllers/`, `routes/`, `middlewares/`, `services/`, `utils/`)
  - [x] Configuração extraída para módulo de config (`config/settings.py`)
  - [x] Models criados/refatorados para abstrair dados (`models/task.py`, `models/user.py`, `models/category.py` sem vazar `password`)
  - [x] Views/Routes separadas para roteamento (`routes/task_routes.py`, `routes/user_routes.py`, `routes/category_routes.py`, `routes/report_routes.py`)
  - [x] Controllers concentram o fluxo da aplicação (`controllers/task_controller.py`, `controllers/user_controller.py`, `controllers/category_controller.py`, `controllers/report_controller.py`)
  - [x] Error handling centralizado (`middlewares/error_handler.py`)
  - [x] Entry point claro (`app.py`)
  - [x] Aplicação inicia sem erros
  - [x] Endpoints originais respondem corretamente

---

### 3.4 Logs Reais de Validação das Aplicações Rodando Pós-Refatoração

#### Log de Execução e Validação — Projeto 1 (`code-smells-project`)
```text
$ curl -s http://localhost:5000/health
{"ambiente":"producao","counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","db_path":"loja.db","debug":false,"status":"ok","versao":"1.0.0"}

$ curl -s "http://localhost:5000/produtos/busca?q=Gamer&categoria=informatica"
{"dados":[{"ativo":1,"categoria":"informatica","descricao":"Notebook potente para jogos","estoque":10,"id":1,"nome":"Notebook Gamer","preco":5999.99},{"ativo":1,"categoria":"informatica","descricao":"Headset com microfone","estoque":25,"id":5,"nome":"Headset Gamer","preco":199.9}],"sucesso":true,"total":2}

$ curl -s -X POST http://localhost:5000/pedidos -H "Content-Type: application/json" -d '{"usuario_id": 1, "itens": [{"produto_id": 1, "quantidade": 1}, {"produto_id": 2, "quantidade": 2}]}'
{"dados":{"pedido_id":1,"total":6179.79},"mensagem":"Pedido criado com sucesso","sucesso":true}

$ curl -s -X PUT http://localhost:5000/pedidos/1/status -H "Content-Type: application/json" -d '{"status": "aprovado"}'
{"mensagem":"Status atualizado","sucesso":true}

$ curl -s http://localhost:5000/relatorios/vendas
{"dados":{"desconto_aplicavel":308.99,"faturamento_bruto":6179.79,"faturamento_liquido":5870.8,"pedidos_aprovados":1,"pedidos_cancelados":0,"pedidos_pendentes":0,"ticket_medio":6179.79,"total_pedidos":1},"sucesso":true}
```

#### Log de Execução e Validação — Projeto 2 (`ecommerce-api-legacy`)
```text
LMS API (MVC) rodando na porta 3000...
[INFO] Processando pagamento para cartão ****-****-****-4444
[INFO] Processando pagamento para cartão ****-****-****-4444

$ curl -s -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" -d '{"usr": "Guilherme", "eml": "gui@fullcycle.com.br", "pwd": "senhaforte", "c_id": 2, "card": "4111222233334444"}'
{"msg":"Sucesso","enrollment_id":2}

$ curl -s -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" -d '{"usr": "João", "eml": "joao@teste.com", "pwd": "123", "c_id": 1, "card": "5111222233334444"}'
Pagamento recusado (HTTP 400)

$ curl -s http://localhost:3000/api/admin/financial-report
[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},{"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}]

$ curl -s -X DELETE http://localhost:3000/api/users/1
Usuário e registros dependentes removidos com sucesso. (HTTP 200)
```

#### Log de Execução e Validação — Projeto 3 (`task-manager-api`)
```text
2026-10-24 00:32:27,531 [INFO] task_manager_api: Seed concluído: 3 usuários, 4 categorias, 10 tasks

$ curl -s http://localhost:5001/health
{"status":"ok","timestamp":"2026-10-24 03:32:29.583793"}

$ curl -s -X POST http://localhost:5001/login -H "Content-Type: application/json" -d '{"email": "joao@email.com", "password": "1234"}'
{"message":"Login realizado com sucesso","token":"eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4ifQ.atwmzQ.6pZi-UcR-GmMoZxTOkbnBkUyTBc","user":{"active":true,"created_at":"2026-10-24 03:32:27.515415","email":"joao@email.com","id":1,"name":"João Silva","role":"admin"}}

$ curl -s http://localhost:5001/tasks/stats
{"cancelled":1,"completion_rate":10.0,"done":1,"in_progress":2,"overdue":2,"pending":6,"total":10}

$ curl -s http://localhost:5001/reports/user/1
{"statistics":{"cancelled":0,"completion_rate":0.0,"done":0,"high_priority":2,"in_progress":0,"overdue":2,"pending":4,"total_tasks":4},"user":{"email":"joao@email.com","id":1,"name":"João Silva"}}
```

---

### 3.5 Observações sobre o Comportamento da Skill em Stacks Diferentes

1. **Adaptação entre Python/Flask (SQLite puro vs. SQLAlchemy ORM) e Node.js/Express**:
   - No **Projeto 1 (`code-smells-project`)**, a skill identificou o uso de `sqlite3` puro procedural em 4 arquivos, extraindo o gerenciamento de conexão para `flask.g` com `teardown_appcontext` e convertendo concatenações de string para tuplas parametrizadas `?`.
   - No **Projeto 2 (`ecommerce-api-legacy`)**, a skill lidou com uma arquitetura orientada a objetos disfuncional (`AppManager.js`) e assincronismo baseado em callbacks do Node.js, introduzindo um cliente SQLite promisificado com suporte a transações (`BEGIN`/`COMMIT`/`ROLLBACK`) e injeção de dependência via construtor nos Models e Controllers.
   - No **Projeto 3 (`task-manager-api`)**, onde já havia `models/` (SQLAlchemy) e `routes/` (Blueprints), a skill reconheceu a organização parcial, preservou os Models existentes (corrigindo o hash MD5, o vazamento de `password` e os métodos ignorados), separou `category_routes.py` de `report_routes.py`, introduziu a camada ausente `controllers/` e modernizou todas as chamadas `Model.query.get()` e `datetime.utcnow()`.

---

## 4. Como Executar

### 4.1 Pré-requisitos

- **Python 3.10+** (com `venv` e `pip`)
- **Node.js 18+** e **npm**
- **Agente de IA com suporte a Skills**: Claude Code (`claude`), Antigravity (`agy`) ou Gemini CLI

### 4.2 Invocando a Skill `refactor-arch` em Cada Projeto

A skill está instalada em `.claude/skills/refactor-arch/` dentro de cada um dos 3 projetos (e em `.agents/skills/refactor-arch/` na raiz):

```bash
# Projeto 1 — code-smells-project (Python/Flask)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — ecommerce-api-legacy (Node.js/Express)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — task-manager-api (Python/Flask + SQLAlchemy)
cd ../task-manager-api
claude "/refactor-arch"
```

### 4.3 Executando e Validando as Aplicações Refatoradas

#### 1. `code-smells-project` (Python/Flask)
```bash
cd code-smells-project
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
# Em outro terminal:
curl http://localhost:5000/health
curl http://localhost:5000/produtos
curl http://localhost:5000/relatorios/vendas
```

#### 2. `ecommerce-api-legacy` (Node.js/Express)
```bash
cd ecommerce-api-legacy
npm install
npm start
# Em outro terminal:
curl http://localhost:3000/api/admin/financial-report
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
```

#### 3. `task-manager-api` (Python/Flask)
```bash
cd task-manager-api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py
.venv/bin/python app.py
# Em outro terminal:
curl http://localhost:5000/health
curl http://localhost:5000/tasks
curl http://localhost:5000/reports/summary
```

