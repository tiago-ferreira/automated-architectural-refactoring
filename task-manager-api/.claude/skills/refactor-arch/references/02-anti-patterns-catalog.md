# 02 — Catálogo de Anti-Patterns e Code Smells (Fase 2)

Este documento define o catálogo oficial de **12 anti-patterns** distribuídos nas 4 severidades (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) para a **Fase 2 — Auditoria Arquitetural** da skill `refactor-arch`.

---

## Escala de Classificação de Severidades

- **CRITICAL**: Falhas graves de arquitetura ou segurança que impedem o funcionamento seguro, expõem dados sensíveis (ex.: credenciais hardcoded, vazamento de senhas/cartões, SQL Injection, criptografia quebrada) ou violam completamente a separação de responsabilidades (ex.: "God Class" / "God Module" contendo banco de dados, regras de negócio complexas e roteamento no mesmo lugar).
- **HIGH**: Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex.: lógicas de negócio e persistência presas dentro de Routes/Controllers, forte acoplamento sem Injeção de Dependência, Callback Hell sem transações, ou estado global mutável compartilhado).
- **MEDIUM**: Problemas de padronização, uso de APIs deprecated/obsoletas, duplicação de código ou gargalos de performance moderada (ex.: Queries N+1 em loops, falta de error handler centralizado, `except:` genérico, validações ausentes).
- **LOW**: Melhorias de legibilidade, nomenclatura críptica de variáveis, "magic numbers" soltos pelo código, imports inutilizados, código morto ou logging improvisado com `print()`/`console.log()`.

---

## Catálogo Detalhado de Anti-Patterns (12 Padrões)

### 1. [CRITICAL] SQL Injection & Unsanitized Raw Queries
- **Sinais de Detecção**:
  - Concatenação de strings (`+`), `f-strings`, `.format()` ou template literals (`` `${}` ``) diretamente na montagem de instruções SQL (`SELECT`, `INSERT`, `UPDATE`, `DELETE`).
  - Exemplo Python: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))` ou `"SELECT * FROM usuarios WHERE email = '" + email + "'"`
  - Endpoints administrativos que recebem e executam SQL cru enviado no corpo da requisição (ex.: `cursor.execute(dados.get("sql"))` em `/admin/query`).
- **Impacto**: Permite leitura, modificação ou destruição completa do banco de dados e bypass de autenticação.
- **Recomendação**: Substituir 100% das concatenações por **Parameterized Queries** (`?` no `sqlite3` Python/Node.js passando tupla/array de parâmetros) ou queries parametrizadas via ORM (SQLAlchemy), e remover/bloquear execução arbitrária de DDL/DML via payload.

---

### 2. [CRITICAL] Hardcoded Credentials & Sensitive Data Exposure
- **Sinais de Detecção**:
  - Chaves secretas, senhas de banco, chaves de API/gateway ou senhas SMTP fixadas em literais no código:
    - `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` ou `'super-secret-key-123'`
    - `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_..."`, `self.email_password = 'senha123'`
  - Exposição de dados sensíveis em respostas JSON ou logs:
    - Retornar `secret_key` no endpoint `/health`.
    - Incluir `'password': self.password` ou `'senha': row['senha']` em métodos `to_dict()` ou listagens de usuários (`GET /usuarios`, `GET /users/<id>`, `POST /login`).
    - Logar número completo de cartão de crédito (`cc`) e chave do gateway no console (`console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`).
- **Impacto**: Vazamento imediato de credenciais de produção, violação de LGPD/PCI-DSS e comprometimento de sessões/tokens.
- **Recomendação**: Extrair todas as configurações e segredos para um módulo `config/` que leia variáveis de ambiente (`os.environ.get` / `process.env`), mascarar/remover dados sensíveis de logs e jamais serializar campos `password`/`senha` ou `secret_key` nas respostas da API.

---

### 3. [CRITICAL] God Class / God Module (Monolithic Anti-Pattern)
- **Sinais de Detecção**:
  - Classe única (ex.: `class AppManager` em `AppManager.js`) que instancia conexão com banco, cria tabelas, faz seed, registra rotas Express, executa lógica de pagamento/checkout e gera relatórios.
  - Arquivo monolítico (ex.: `models.py` com >300 linhas ou `controllers.py` com ~300 linhas) que mistura 3 ou mais domínios distintos (`produtos`, `usuarios`, `pedidos`, `relatorios`) além de regras de desconto, notificações e acesso direto ao banco.
- **Impacto**: Viola frontalmente o Single Responsibility Principle (SRP); torna impossível testar camadas isoladamente e qualquer alteração gera efeito colateral em todo o sistema.
- **Recomendação**: Decompor a God Class / God Module nas camadas do padrão **MVC** por domínio: `models/` (um arquivo por entidade), `controllers/` (orquestração de negócio por domínio), `views/` ou `routes/` (roteamento HTTP) e `config/` (banco e variáveis de ambiente).

---

### 4. [CRITICAL] Broken / Weak Cryptography & Fake Authentication Tokens
- **Sinais de Detecção**:
  - Armazenamento e comparação de senhas em texto puro (`senha = '123456'`).
  - Uso de algoritmos de hash criptograficamente quebrados e sem salt como `hashlib.md5(pwd.encode()).hexdigest()`.
  - Funções caseiras de "criptografia" baseadas em codificação reversível como `Buffer.from(pwd).toString('base64')` em loops síncronos bloqueantes (`badCrypto`).
  - Geração de tokens falsos e previsíveis concatenando o ID do usuário (`'fake-jwt-token-' + str(user.id)`).
- **Impacto**: Senhas facilmente revertidas via Rainbow Tables ou decodificação direta, e falsificação trivial de identidade (account takeover) alterando o ID no token.
- **Recomendação**: Utilizar funções de derivação de chave seguras com salt (ex.: `werkzeug.security.generate_password_hash` / `check_password_hash` ou `crypto.scryptSync` / `pbkdf2Sync` com comparação `timingSafeEqual`) e gerar tokens assinados com HMAC (`itsdangerous` / `crypto.createHmac`) usando a `SECRET_KEY` do ambiente.

---

### 5. [HIGH] Fat Routes / Fat Controllers & Missing Controller Layer
- **Sinais de Detecção**:
  - Arquivos de rotas (`routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py` ou `AppManager.setupRoutes`) que executam diretamente queries ORM/SQL (`Task.query.all()`, `db.session.add()`, `db.session.commit()`), cálculos estatísticos, formatação de dados e regras de domínio sem passar por um Controller.
  - Controllers (`controllers.py`) que abrem cursores SQL diretamente (`db = get_db(); cursor = db.cursor()` em `health_check` ou `app.py` em `/admin/reset-db` e `/admin/query`).
  - Mistura de domínios não relacionados no mesmo arquivo de rota (ex.: CRUD de `/categories` dentro de `routes/report_routes.py`).
- **Impacto**: Acopla a camada de transporte HTTP (Flask/Express) às regras de negócio e ao banco de dados, impedindo o reuso da lógica e violando a separação MVC.
- **Recomendação**: Introduzir/limpar a camada `controllers/` para concentrar todo o fluxo de negócio, deixando `views/` (`routes/`) apenas com extração de request e retorno de status/JSON, e `models/` com a persistência e regras da entidade. Separar domínios misturados em seus próprios módulos (`category_controller.py`, `category_routes.py`).

---

### 6. [HIGH] Tight Coupling, Callback Hell & Missing Transaction Integrity
- **Sinais de Detecção**:
  - Encadeamento profundo de callbacks assíncronos (>3 níveis, "Pyramid of Doom") misturando `this.db` e `self.db` (ex.: `POST /api/checkout` em `AppManager.js:28-78`).
  - Operações de escrita em múltiplas tabelas (ex.: criar pedido + inserir itens + baixar estoque, ou criar matrícula + pagamento + log de auditoria) sem bloco transacional atômico (`BEGIN` / `COMMIT` / `ROLLBACK`).
  - Exclusão de registros pai sem remover ou desvincular registros dependentes (ex.: `DELETE /api/users/:id` em `AppManager.js:131-137`, que apaga o usuário e deixa matrículas e pagamentos órfãos).
  - Instanciação direta de dependências concretas dentro de handlers sem Injeção de Dependência.
- **Impacto**: Falhas parciais no meio do fluxo corrompem o estado do banco (ex.: estoque descontado sem pedido válido, ou matrícula sem pagamento) e dificultam testes unitários com mocks.
- **Recomendação**: Encapsular chamadas assíncronas do banco em Promises (`async/await`), envolver operações multi-tabela em transações atômicas e garantir remoção/atualização em cascata das dependências antes de deletar uma entidade pai.

---

### 7. [HIGH] Mutable Global State & Thread-Unsafe Connections
- **Sinais de Detecção**:
  - Conexão única de banco de dados armazenada em variável global mutável (`db_connection = None` com `sqlite3.connect(..., check_same_thread=False)` em `database.py:4-10`) compartilhada entre todas as threads/requests.
  - Objetos globais em memória usados como cache ou acumuladores sem controle de concorrência ou limite de memória (`let globalCache = {}; let totalRevenue = 0;` em `src/utils.js:9-15`).
- **Impacto**: Condições de corrida (race conditions), corrupção de cursores SQLite sob requisições simultâneas e vazamento de memória (memory leak).
- **Recomendação**: Gerenciar conexões no escopo da requisição (`flask.g` com `teardown_appcontext` em Flask, ou instância gerenciada injetada nos Models em Node.js) e encapsular qualquer cache em um serviço/repositório controlado com limite de tamanho (bounded cache) e responsabilidade única.

---

### 8. [MEDIUM] N+1 Query Problem & Inefficient In-Memory Aggregations
- **Sinais de Detecção**:
  - Execução de queries SQL ou chamadas ORM (`cursor.execute`, `this.db.all`, `this.db.get`, `User.query.get`, `Task.query.filter_by`) **dentro de loops** (`for`, `forEach`, `map`):
    - `models.py:139-166` e `177-232`: buscar itens de cada pedido em loop e depois o nome do produto de cada item em outro loop aninhado.
    - `AppManager.js:89-127`: buscar `enrollments` por curso em loop e depois `users` e `payments` por matrícula em loop aninhado.
    - `routes/task_routes.py:42, 51`: chamar `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` dentro do loop de `GET /tasks`.
    - `routes/report_routes.py:55-68` e `161-164`: buscar tasks por usuário e contagem por categoria dentro de loops `for`, além de carregar todas as linhas com `.all()` apenas para contar registros em Python.
- **Impacto**: Degradação exponencial de performance ($O(N)$ ou $O(N \times M)$ round-trips ao banco de dados para uma única requisição HTTP).
- **Recomendação**: Substituir queries em loops por `JOIN`s SQL (`LEFT JOIN`), `eager loading` (`joinedload` no SQLAlchemy) ou agregações `GROUP BY` / `CASE WHEN` diretamente no banco de dados.

---

### 9. [MEDIUM] Deprecated APIs Usage (Obsolete Framework/Language Calls)
- **Sinais de Detecção**:
  - **SQLAlchemy 2.0 Legacy Query API**: Uso de `Model.query.get(id)` (ex.: `Task.query.get(task_id)`, `User.query.get(user_id)`, `Category.query.get(cat_id)`), que foi depreciado no SQLAlchemy 2.0 (`LegacyAPIWarning`).
  - **Python 3.12+ Naive UTC Datetime**: Uso de `datetime.utcnow()` (ex.: `default=datetime.utcnow`, `datetime.utcnow() - timedelta(...)`), depreciado no Python 3.12+ por produzir objetos `datetime` ingênuos (sem `tzinfo`).
  - **Node.js / Express Deprecated Calls**: Uso de `new Buffer()` ou métodos legados substituídos por `Buffer.from()`.
- **Impacto**: Gera warnings em tempo de execução, bugs de fuso horário (timezone-naive vs timezone-aware) e quebra total ao atualizar versões menores do Python ou SQLAlchemy.
- **Recomendação**:
  - Substituir `Model.query.get(id)` por `db.session.get(Model, id)`.
  - Substituir `datetime.utcnow()` por uma função utilitária baseada em `datetime.now(timezone.utc)` (normalizando para UTC consistente com o banco).

---

### 10. [MEDIUM] Missing Centralized Error Handling, Bare `except:` & Duplicated Validation
- **Sinais de Detecção**:
  - Cláusulas `except:` vazias ("bare except") em Python (`except:` sem especificar `Exception` ou `ValueError`), que capturam até sinais de encerramento do processo e mascaram bugs.
  - Repetição de blocos `try ... except Exception as e: return jsonify({"erro": str(e)}), 500` em todas as funções de controller/rota, expondo mensagens internas de erro de banco ao cliente.
  - Callbacks de banco em Node.js que ignoram o parâmetro `err` (ex.: `AppManager.js:92, 104, 106, 133`) e ausência de middleware global `errorHandler(err, req, res, next)`.
  - Duplicação de código de validação e serialização manual entre rotas de criação, atualização e listagem.
- **Impacto**: Comportamento inconsistente em falhas, vazamento de stack traces/erros internos de SQL e requisições penduradas (hanging requests) em caso de falha assíncrona.
- **Recomendação**: Criar um módulo `middlewares/error_handler` centralizado, eliminar todos os `except:` genéricos tratando exceções específicas (`ValueError`, erros de domínio) e centralizar validações e serializações (`to_dict()`) nos Models/Controllers.

---

### 11. [LOW] Magic Numbers, Hardcoded Business Constants & Cryptic Naming
- **Sinais de Detecção**:
  - Variáveis de 1 ou 2 letras que ocultam a intenção do domínio (`u`, `e`, `p`, `cid`, `cc`, `c`, `enr`, `enrId`, `td`).
  - Números mágicos soltos no meio de algoritmos: faixas de faturamento (`10000`, `5000`, `1000`) e alíquotas de desconto (`0.1`, `0.05`, `0.02`), limites de string (`2`, `3`, `200`, `4`), prioridades (`1`, `5`), dias de relatório (`7`) e prefixos de cartão (`"4"`).
- **Impacto**: Dificulta a leitura, aumenta a carga cognitiva durante manutenção e propicia erros ao alterar regras de negócio.
- **Recomendação**: Renomear variáveis para nomes semânticos (`userName`, `email`, `password`, `courseId`, `cardNumber`, `enrollment`) e extrair todos os números mágicos e listas de domínio para constantes nomeadas em `config/`.

---

### 12. [LOW] Dead Code, Unused/Multiple Imports & Ad-hoc `print`/`console.log`
- **Sinais de Detecção**:
  - Imports múltiplos na mesma linha e não utilizados (`import os, sys, json, datetime`, `import json, os, sys, time`, `import math, hashlib`).
  - Classes e funções inteiras nunca chamadas pela aplicação (ex.: `NotificationService` em `services/notification_service.py` e funções/constantes órfãs em `utils/helpers.py`).
  - Condicionais booleanas redundantes (`if cond: return True else: return False`) e checagem de tipo não-idiomática (`type(tags) == list` em vez de `isinstance(tags, list)`).
  - Uso de `print()` ou `console.log()` espalhados nas rotas e controllers para auditoria operacional.
- **Impacto**: Polui a codebase com código morto que confunde desenvolvedores e gera logs despadronizados.
- **Recomendação**: Remover imports não utilizados seguindo a PEP 8 / ESLint, integrar ou remover código morto, simplificar expressões booleanas e utilizar logger estruturado.
