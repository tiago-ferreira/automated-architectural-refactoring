================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1, requests 2.31.0, python-dotenv 1.0.0
Domain:        Task Manager API (tarefas, categorias, usuários e relatórios de produtividade)
Architecture:  Parcialmente organizada em camadas (models, routes, services, utils), mas sem Controllers — lógica de negócio, queries e agregações acopladas diretamente nas rotas (Fat Routes)
Source files:  11 files analyzed (~1,153 lines of code, plus 4 empty __init__.py files)
DB tables:     users, categories, tasks
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Files:   11 analyzed | ~1,153 lines of code

## Summary
CRITICAL: 3 | HIGH: 2 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Secret Key and SMTP Credentials
File: app.py:11-13, services/notification_service.py:7-10
Description: A chave secreta do Flask está hardcoded em `app.py:13` (`app.config['SECRET_KEY'] = 'super-secret-key-123'`) juntamente com a URI fixa do banco (`app.py:11`), e `NotificationService` (`services/notification_service.py:7-10`) armazena credenciais SMTP em texto claro no código (`self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'`).
Impact: Comprometimento da segurança criptográfica da aplicação e exposição de credenciais de e-mail no repositório.
Recommendation: Extrair todas as configurações (`SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`) para `config/settings.py` lendo de variáveis de ambiente (`os.environ.get`).

### [CRITICAL] Broken MD5 Password Hashing, Password Hash Exposure in `User.to_dict()` & Predictable Fake Token
File: models/user.py:16-32, routes/user_routes.py:33, routes/user_routes.py:85, routes/user_routes.py:129, routes/user_routes.py:207-211
Description: O model `User` calcula hashes de senha com MD5 puro sem salt (`hashlib.md5(pwd.encode()).hexdigest()` em `models/user.py:29, 32`). Além disso, `User.to_dict()` (`models/user.py:16-25`) inclui `'password': self.password` na linha 21, vazando o hash de senha nas respostas JSON de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`. Por fim, `POST /login` retorna um token falso previsível `'fake-jwt-token-' + str(user.id)` (`routes/user_routes.py:210`).
Impact: Quebra trivial de senhas via Rainbow Tables, exposição direta do hash em endpoints públicos e falsificação de autenticação (qualquer cliente pode forjar o token de outro `user.id`).
Recommendation: Substituir MD5 por `werkzeug.security.generate_password_hash` / `check_password_hash` (mantendo fallback de verificação para hashes legados), remover `'password'` de `User.to_dict()` e gerar tokens assinados criptograficamente (`itsdangerous.URLSafeTimedSerializer`).

### [CRITICAL] Missing Controller Layer & Fat Routes Manipulating `db.session` Directly
File: routes/task_routes.py:11-299, routes/user_routes.py:10-211, routes/report_routes.py:12-223
Description: Apesar de possuir pastas `models/` e `routes/`, o projeto não possui camada de `controllers/`. Todas as rotas executam queries ORM diretamente (`Task.query`, `User.query`, `Category.query`), manipulam transações (`db.session.add`, `db.session.commit`, `db.session.rollback`), aplicam validações de domínio e calculam relatórios complexos dentro das funções de rota HTTP.
Impact: Viola o padrão MVC, acoplando fortemente a camada de apresentação HTTP (Blueprints Flask) à persistência SQLAlchemy e às regras de negócio.
Recommendation: Criar o pacote `controllers/` (`task_controller.py`, `user_controller.py`, `category_controller.py`, `report_controller.py`) para encapsular toda a lógica de negócio e persistência, reduzindo `routes/` apenas ao transporte HTTP.

### [HIGH] Domain Mixing in `report_routes.py` (Categories CRUD Mixed into Reports)
File: routes/report_routes.py:157-223
Description: Todos os endpoints de CRUD da entidade `Category` (`GET /categories`, `POST /categories`, `PUT /categories/<id>`, `DELETE /categories/<id>`) foram implementados dentro de `routes/report_routes.py` (`linhas 157-223`), misturando gerenciamento cadastral de categorias com relatórios analíticos de tarefas e produtividade.
Impact: Viola o princípio de responsabilidade única (SRP) e coesão de módulos, dificultando a localização e manutenção das rotas de categorias.
Recommendation: Extrair o domínio de categorias para `controllers/category_controller.py` e `routes/category_routes.py` (mantendo as mesmas URLs `/categories` registradas na aplicação).

### [HIGH] Ignored Domain Methods & Severe Duplication of Validation and `overdue` Logic
File: models/task.py:23-60, routes/task_routes.py:17-40, routes/task_routes.py:71-80, routes/task_routes.py:92-145, routes/task_routes.py:166-214, routes/task_routes.py:283-287, routes/user_routes.py:162-180, routes/report_routes.py:33-36, routes/report_routes.py:132-135, utils/helpers.py:57-108
Description: O model `Task` já define `to_dict()`, `validate_status()`, `validate_priority()` e `is_overdue()` (`models/task.py:23-60`), e `utils/helpers.py` define `process_task_data()`, mas as rotas ignoram esses métodos: a montagem manual de dicionário e o cálculo de `overdue` (3 `if`s aninhados) são copiados e colados em 6 lugares diferentes (`task_routes.py:17-40, 71-80, 283-287`, `user_routes.py:162-180`, `report_routes.py:33-36, 132-135`).
Impact: Duplicação massiva de regras de negócio; qualquer mudança no critério de tarefa atrasada (`overdue`) ou validação exige edição manual em múltiplos arquivos.
Recommendation: Centralizar o cálculo em `Task.is_overdue()` e `Task.to_dict(include_relations=...)` no Model e reutilizá-los em todos os Controllers.

### [MEDIUM] Deprecated SQLAlchemy 2.0 (`Query.get`) & Python 3.12+ (`datetime.utcnow`) APIs
File: models/task.py:15-16, models/task.py:52, models/user.py:14, models/category.py:11, routes/task_routes.py:31, routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:72, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188, routes/task_routes.py:195, routes/task_routes.py:215, routes/task_routes.py:227, routes/task_routes.py:285, routes/user_routes.py:29, routes/user_routes.py:94, routes/user_routes.py:136, routes/user_routes.py:155, routes/user_routes.py:172, routes/report_routes.py:35, routes/report_routes.py:42, routes/report_routes.py:45, routes/report_routes.py:71, routes/report_routes.py:105, routes/report_routes.py:133, routes/report_routes.py:192, routes/report_routes.py:213, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-74
Description: Uso generalizado de duas APIs depreciadas: (1) `Model.query.get(id)` (depreciado no SQLAlchemy 2.0 com `LegacyAPIWarning` em 15 chamadas nas rotas) e (2) `datetime.utcnow()` (depreciado no Python 3.12+ em mais de 20 locais em `models/`, `routes/`, `services/`, `utils/` e `seed.py`).
Impact: Emissão constante de `DeprecationWarning` / `LegacyAPIWarning` e incompatibilidade futura com versões recentes do Python e SQLAlchemy.
Recommendation: Substituir todas as chamadas `Model.query.get(id)` por `db.session.get(Model, id)` e substituir `datetime.utcnow()` por um helper `utc_now()` baseado em `datetime.now(timezone.utc)` em `config/settings.py`.

### [MEDIUM] N+1 Query Problem in Task Listing, Categories & Summary Report
File: routes/task_routes.py:14-59, routes/user_routes.py:12-24, routes/report_routes.py:15-68, routes/report_routes.py:159-164
Description: Em `GET /tasks` (`routes/task_routes.py:42, 51`), para cada tarefa retornada são feitas até 2 queries extras (`User.query.get` e `Category.query.get`). Em `GET /users` (`routes/user_routes.py:22`), `len(u.tasks)` dispara lazy loading por usuário. Em `GET /reports/summary` (`routes/report_routes.py:55-68`) e `GET /categories` (`routes/report_routes.py:163`), executa-se 1 query adicional por usuário/categoria dentro de loops `for`, além de 10 queries `COUNT` separadas para cada status e prioridade (`linhas 19-28`).
Impact: Degradação severa de performance com dezenas de queries desnecessárias por requisição.
Recommendation: Utilizar `joinedload(Task.user)` e `joinedload(Task.category)` em `GET /tasks` e agregações `GROUP BY` / `func.count` do SQLAlchemy nos Controllers de usuários, categorias e relatórios.

### [MEDIUM] Bare `except:` Clauses & Missing Centralized Error Handler
File: routes/task_routes.py:62, routes/task_routes.py:137, routes/task_routes.py:204, routes/task_routes.py:236, routes/user_routes.py:130, routes/user_routes.py:149, routes/report_routes.py:186, routes/report_routes.py:207, routes/report_routes.py:221, utils/helpers.py:46, utils/helpers.py:49, utils/helpers.py:88
Description: Existência de 12 blocos `except:` vazios ("bare except") que capturam qualquer exceção (incluindo `SystemExit` e `KeyboardInterrupt`) e ocultam a causa real do erro, além da ausência de um módulo `middlewares/error_handler.py` registrado no Flask.
Impact: Dificulta o diagnóstico de falhas em produção e viola boas práticas da PEP 8 (E722).
Recommendation: Substituir todos os `except:` por exceções específicas (`except ValueError:`, `except SQLAlchemyError:`, `except Exception as exc:`) e criar `middlewares/error_handler.py`.

### [MEDIUM] Unhandled `ValueError` in `/tasks/search` Query Parameters
File: routes/task_routes.py:260-264
Description: Em `GET /tasks/search`, os parâmetros de query string `priority` e `user_id` são convertidos diretamente com `int(priority)` (`linha 261`) e `int(user_id)` (`linha 264`) sem validação ou tratamento de `ValueError`.
Impact: Enviar `?priority=alta` ou `?user_id=abc` causa uma exceção não tratada e retorna HTTP 500 Internal Server Error em vez de HTTP 400 Bad Request.
Recommendation: Validar e converter `priority` e `user_id` com tratamento de `ValueError` no `TaskController`, retornando erro 400 amigável quando inválidos.

### [LOW] Unused Imports, One-Line Multiple Imports & Dead Code
File: app.py:7, models/task.py:3, routes/task_routes.py:7, routes/user_routes.py:5-6, routes/report_routes.py:7-8, utils/helpers.py:3-7, services/notification_service.py:1-48
Description: Múltiplos imports na mesma linha e não utilizados (`import os, sys, json, datetime` em `app.py:7`, `import json, os, sys, time` em `task_routes.py:7`, `import hashlib, json, re` em `user_routes.py:6`, `import math, hashlib` em `utils/helpers.py:6-7`). Adicionalmente, `NotificationService` e quase todo o arquivo `utils/helpers.py` são código morto nunca chamado.
Impact: Poluição do namespace, violação da PEP 8 (E401/F401) e custo cognitivo desnecessário.
Recommendation: Remover todos os imports inutilizados e integrar as funções úteis de `utils/helpers.py` e `config/settings.py` aos Controllers.

### [LOW] Non-Idiomatic Type Checks (`type(x) == list`) & Redundant Boolean Returns
File: models/task.py:40-43, models/task.py:46-48, models/task.py:51-60, models/user.py:35-38, routes/task_routes.py:141, routes/task_routes.py:210, utils/helpers.py:21-23, utils/helpers.py:53-55, utils/helpers.py:103
Description: Uso de `type(tags) == list` em vez de `isinstance(tags, list)` (`task_routes.py:141, 210`, `helpers.py:103`) e estruturas redundantes `if cond: return True else: return False` (`models/task.py:40-60`, `models/user.py:35-38`, `utils/helpers.py:21-23, 53-55`).
Impact: Código verboso e não-idiomático em Python.
Recommendation: Simplificar retornos booleanos para `return bool(cond)` e utilizar `isinstance(tags, list)`.

### [LOW] Magic Numbers and Hardcoded Validation Literals Across Routes
File: routes/task_routes.py:96, routes/task_routes.py:99, routes/task_routes.py:110, routes/task_routes.py:113, routes/user_routes.py:64, routes/user_routes.py:71, routes/report_routes.py:45, routes/report_routes.py:129
Description: Embora `utils/helpers.py:110-116` defina constantes (`VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`), as rotas repetem literais mágicos (`3`, `200`, `1`, `5`, `4`, `7`, `['pending', ...]`, `['user', 'admin', 'manager']`).
Impact: Inconsistência potencial entre regras de validação espalhadas em diferentes rotas.
Recommendation: Mover as constantes de domínio para `config/settings.py` e referenciá-las em todos os Models e Controllers.

================================
Total: 12 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
