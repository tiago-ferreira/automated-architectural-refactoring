# 01 — Heurísticas de Análise de Projeto (Fase 1)

Este documento define as heurísticas agnósticas de tecnologia que a skill `refactor-arch` deve seguir na **Fase 1 (`PHASE 1: PROJECT ANALYSIS`)** para mapear qualquer codebase de backend antes de iniciar a auditoria.

---

## 1. Detecção de Linguagem e Ecossistema

Inspecione os arquivos de manifesto na raiz do projeto (e subdiretórios imediatos) seguindo esta tabela de sinais:

| Arquivo Manifesto / Extensão | Linguagem Detectada | Gerenciador de Pacotes | Arquivos de Código-Fonte a Contabilizar |
|---|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | **Python** | `pip` / `poetry` / `pipenv` | Todos os arquivos `*.py` (exceto `.venv/`, `venv/`, `__pycache__/`) |
| `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` | **JavaScript / Node.js** (ou **TypeScript** se `tsconfig.json` existir) | `npm` / `yarn` / `pnpm` | Todos os arquivos `*.js`, `*.ts` (exceto `node_modules/`, `dist/`, `build/`) |
| `go.mod`, `go.sum` | **Go** | `go mod` | Todos os arquivos `*.go` (exceto `vendor/`) |
| `pom.xml`, `build.gradle` | **Java / Kotlin** | `Maven` / `Gradle` | Todos os arquivos `*.java`, `*.kt` em `src/main/` |
| `composer.json` | **PHP** | `Composer` | Todos os arquivos `*.php` (exceto `vendor/`) |
| `Gemfile` | **Ruby** | `Bundler` | Todos os arquivos `*.rb` (exceto `vendor/`) |

> **Regra de Contagem de Arquivos (`Source files`)**:
> Contabilize **apenas** os arquivos de código-fonte da linguagem principal do projeto (ex.: `.py` ou `.js`), ignorando pastas de dependências (`node_modules`, `.venv`, `venv`), diretórios de agentes (`.claude`, `.agents`), arquivos de lock, bancos `.db` e `README.md`. Caso existam pacotes `__init__.py` vazios (0 linhas), indique claramente se foram ou não incluídos na contagem.

---

## 2. Detecção de Framework Web e Dependências

Extraia do manifesto (`requirements.txt` ou `package.json`) e dos imports do entry point (`app.py`, `main.py`, `src/app.js`, `server.js`, `index.js`) o framework principal e sua versão exata:

- **Python**:
  - `flask==X.Y.Z` ou `from flask import Flask` → **Flask X.Y.Z**
  - `fastapi` → **FastAPI**
  - `django` → **Django**
  - Dependências complementares relevantes: `flask-cors`, `flask-sqlalchemy`, `marshmallow`, `requests`, `python-dotenv`, `sqlite3` (stdlib).
- **Node.js**:
  - `"express": "^X.Y.Z"` ou `require('express')` → **Express X.Y.Z**
  - `"fastify"` → **Fastify**
  - `"@nestjs/core"` → **NestJS**
  - Dependências complementares relevantes: `sqlite3`, `pg`, `mongoose`, `cors`, `dotenv`.

---

## 3. Detecção de Banco de Dados e Tabelas/Entidades

Mapeie a camada de persistência procurando por:

1. **Drivers e Conexões**:
   - `import sqlite3` / `sqlite3.connect("loja.db")` → SQLite (arquivo local)
   - `new sqlite3.Database(':memory:')` → SQLite in-memory
   - `SQLAlchemy()` / `SQLALCHEMY_DATABASE_URI = 'sqlite:///tasks.db'` → SQLite via SQLAlchemy ORM
2. **Descoberta de Tabelas (`DB tables`)**:
   - Busque declarações DDL: `CREATE TABLE [IF NOT EXISTS] <nome_tabela>`
   - Busque modelos ORM: classes herdando de `db.Model` ou `Base` com `__tablename__ = '<nome_tabela>'`
   - Liste todas as tabelas encontradas em ordem lógica de domínio (ex.: `produtos, usuarios, pedidos, itens_pedido` ou `users, courses, enrollments, payments, audit_logs` ou `users, categories, tasks`).

---

## 4. Identificação do Domínio da Aplicação

Combine as tabelas do banco, nomes de rotas (`@app.route`, `@bp.route`, `app.get`, `app.post`, `app.add_url_rule`) e entidades para descrever o domínio em 1 linha clara:

- **Sinais de E-commerce API**: rotas `/produtos`, `/pedidos`, `/usuarios`, `/relatorios/vendas` → *E-commerce API (produtos, pedidos, usuários, relatórios de vendas)*.
- **Sinais de LMS / Checkout API**: tabelas `courses`, `enrollments`, `payments` e rotas `/api/checkout`, `/api/admin/financial-report` → *LMS / Course E-commerce API (cursos, matrículas, checkout/pagamentos e relatório financeiro)*.
- **Sinais de Task Manager API**: tabelas `tasks`, `categories`, `users` e rotas `/tasks`, `/categories`, `/users`, `/reports` → *Task Manager API (tarefas, categorias, usuários e relatórios de produtividade)*.

---

## 5. Diagnóstico da Arquitetura Atual

Avalie a distribuição de responsabilidades entre os arquivos e classifique em um dos 3 perfis arquiteturais:

### Perfil A — Monolítica / Procedural em Poucos Arquivos
- **Sinais**: Todos os arquivos na raiz (`app.py`, `controllers.py`, `models.py`, `database.py`), sem subdiretórios por camada; um único `models.py` ou `controllers.py` concentra múltiplos domínios distintos; rotas definidas no mesmo arquivo que queries SQL.
- **Diagnóstico padrão**: `Monolítica — tudo em N arquivos na raiz, sem separação real de camadas por domínio`.

### Perfil B — Centrada em God Class (Frankenstein Monolith)
- **Sinais**: Uma única classe central (ex.: `AppManager.js`) instancia o banco de dados, cria tabelas, faz seed, registra rotas HTTP, processa regras de negócio/pagamento e executa queries aninhadas.
- **Diagnóstico padrão**: `Monolítica centrada em God Class (AppManager) — banco de dados, rotas, regras de negócio e relatórios acoplados em uma única classe`.

### Perfil C — Parcialmente Organizada em Camadas (Incompleta / Fat Routes)
- **Sinais**: Já existem pastas como `models/`, `routes/`, `services/`, `utils/`, porém **falta a camada `controllers/`** (ou as rotas acessam diretamente `db.session` e `Model.query` ignorando services/controllers), ou um mesmo arquivo de rota mistura domínios diferentes (ex.: `report_routes.py` gerenciando CRUD de `/categories`).
- **Diagnóstico padrão**: `Parcialmente organizada em camadas (models, routes, services, utils), mas sem Controllers — lógica de negócio, queries e agregações acopladas diretamente nas rotas (Fat Routes)`.
