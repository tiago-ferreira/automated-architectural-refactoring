# 04 — Guidelines de Arquitetura MVC para APIs Backend (Fase 3)

Este documento define as diretrizes arquiteturais do padrão **MVC (Model-View-Controller)** que a skill `refactor-arch` deve aplicar durante a **Fase 3 — Refatoração**.

---

## 1. Visão Geral das Camadas MVC em APIs REST

Em aplicações de backend/APIs REST (sem renderização de HTML server-side), as responsabilidades do padrão MVC + infraestrutura transversal são divididas estritamente da seguinte maneira:

```text
[ HTTP Client ]
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ Views / Routes (views/ ou routes/)                       │
│  - Define endpoints HTTP (Flask Blueprints / Express)    │
│  - Extrai query params, path params e body JSON          │
│  - Chama o Controller correspondente e formata o HTTP    │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│ Controllers (controllers/)                               │
│  - Orquestra o fluxo da aplicação e regras de negócio    │
│  - Valida invariantes de entrada e coordena transações   │
│  - Invoca um ou mais Models; livre de detalhes de SQL    │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│ Models (models/)                                         │
│  - Abstrai as entidades de domínio e o acesso a dados    │
│  - Executa queries SQL parametrizadas ou operações ORM   │
│  - Contém métodos de validação/serialização da entidade  │
└──────────────────────────────────────────────────────────┘
```

### Camadas de Suporte Obrigatórias
- **Config (`config/`)**: Centraliza leitura de variáveis de ambiente (`SECRET_KEY`, credenciais, porta, caminho do banco) e constantes de domínio (limites, alíquotas, listas de status/categorias válidas). **Zero segredos hardcoded no código.**
- **Middlewares (`middlewares/`)**: Centraliza o tratamento de erros HTTP/exceções (`error_handler`), evitando blocos `try/except` repetitivos que vazam detalhes internos.
- **Composition Root (`app.py` / `src/app.js`)**: Ponto de entrada limpo que instancia a aplicação, carrega `config`, inicializa o banco de dados, registra blueprints/rotas e registra os middlewares de erro.

---

## 2. Regras de Responsabilidade e Fronteiras (O que PODE e o que NÃO PODE)

| Camada | O que DEVE conter | O que é PROIBIDO conter |
|---|---|---|
| **Config (`config/`)** | Variáveis lidas via `os.environ.get()` / `process.env`, constantes nomeadas de negócio, inicialização/conexão segura de banco de dados. | Segredos de produção fixos sem leitura de ambiente; lógica de negócio. |
| **Models (`models/`)** | Classes/módulos por entidade de domínio (`ProdutoModel`, `UsuarioModel`, `PedidoModel`, `CourseModel`, `Task`, etc.), queries SQL 100% parametrizadas (`?`) ou ORM moderno (`db.session.get`), `JOIN`s eficientes e serialização segura (`to_dict()` sem campo `password`/`senha`). | Acesso aos objetos HTTP (`flask.request`, `jsonify`, `req`, `res`), códigos de status HTTP (`400`, `404`, `500`) ou concatenação de strings em SQL. |
| **Controllers (`controllers/`)** | Orquestração de casos de uso (ex.: validar dados de entrada, verificar estoque, calcular totais/descontos, coordenar múltiplos Models, acionar serviços auxiliares). | Queries SQL cruas (`cursor.execute("SELECT...")`), manipulação direta de `db.session.add/commit` fora da camada de dados/transação, ou definição de rotas HTTP. |
| **Views / Routes (`views/` ou `routes/`)** | Definição de rotas/Blueprints/Routers, leitura de `request.get_json()` / `req.body` / `req.params`, delegação ao Controller e retorno da resposta HTTP (`jsonify(...)`, `res.status(...).json(...)`). | Regras de negócio, cálculos financeiros, loops de agregação ou acesso direto ao banco de dados / Models. |
| **Middlewares (`middlewares/`)** | Handlers globais de exceções (`@app.errorhandler` no Flask ou `(err, req, res, next)` no Express), erros customizados (`ValidationError`, `NotFoundError`, `ConflictError`). | Regras específicas de um único endpoint. |

---

## 3. Estruturas de Diretórios Alvo por Stack e Nível de Organização

A skill deve adaptar a árvore de diretórios respeitando o entry point original de cada projeto:

### 3.1 Projeto Python/Flask Monolítico (ex.: `code-smells-project`)
Mantém `app.py` na raiz como Composition Root e organiza os pacotes MVC:

```text
code-smells-project/
├── config/
│   ├── __init__.py
│   └── settings.py            # Variáveis de ambiente, constantes de negócio e conexão DB por request (flask.g)
├── models/
│   ├── __init__.py
│   ├── produto_model.py       # Queries parametrizadas de produtos
│   ├── usuario_model.py       # Queries parametrizadas de usuários e hash seguro de senha
│   └── pedido_model.py        # Queries parametrizadas de pedidos, itens (com JOIN sem N+1) e relatórios
├── controllers/
│   ├── __init__.py
│   ├── produto_controller.py  # Validação e fluxo de negócio de produtos
│   ├── usuario_controller.py  # Validação, criação e autenticação de usuários
│   └── pedido_controller.py   # Orquestração de pedidos, status e relatório de vendas
├── views/
│   ├── __init__.py
│   └── routes.py              # Flask Blueprints/rotas HTTP delegando para os controllers
├── middlewares/
│   ├── __init__.py
│   └── error_handler.py       # Tratamento centralizado de erros HTTP e exceções
├── database.py                # Facade compatível delegando para config/settings.py
└── app.py                     # Composition root enxuto
```

### 3.2 Projeto Node.js/Express Centrado em God Class (ex.: `ecommerce-api-legacy`)
Mantém `src/app.js` como Composition Root (conforme `"main": "src/app.js"` no `package.json`) e decompõe a God Class em MVC:

```text
ecommerce-api-legacy/
├── src/
│   ├── config/
│   │   ├── settings.js        # Variáveis de ambiente (process.env), constantes e logger/crypto seguros
│   │   └── database.js        # Inicialização SQLite com suporte a Promises (run/get/all) e transações
│   ├── models/
│   │   ├── courseModel.js     # Acesso a dados de cursos
│   │   ├── userModel.js       # Acesso a dados de usuários e exclusão limpa em cascata
│   │   ├── enrollmentModel.js # Acesso a matrículas, pagamentos e logs de auditoria
│   │   └── reportModel.js     # Relatório financeiro otimizado via SQL JOIN (zero N+1)
│   ├── controllers/
│   │   ├── checkoutController.js # Orquestração de checkout, validação e pagamento
│   │   ├── reportController.js   # Orquestração do relatório financeiro
│   │   └── userController.js     # Orquestração de exclusão de usuário com integridade referencial
│   ├── views/
│   │   └── routes.js          # Express Router mapeando endpoints para os controllers (com arrow functions)
│   ├── middlewares/
│   │   └── errorHandler.js    # Middleware centralizado de erros Express
│   └── app.js                 # Composition root (exporta e inicia o app)
└── package.json
```

### 3.3 Projeto Python/Flask Parcialmente Organizado (ex.: `task-manager-api`)
Preserva os pacotes existentes (`models/`, `routes/`, `services/`, `utils/`), adiciona as camadas ausentes (`config/`, `controllers/`, `middlewares/`) e separa domínios misturados:

```text
task-manager-api/
├── config/
│   ├── __init__.py
│   └── settings.py            # Configurações via os.environ, constantes de domínio e helper UTC moderno
├── models/
│   ├── __init__.py
│   ├── task.py                # Model Task com timezone-aware UTC e métodos de domínio utilizados
│   ├── user.py                # Model User com hash seguro (Werkzeug/PBKDF2) e to_dict() sem senha
│   └── category.py            # Model Category limpo
├── controllers/
│   ├── __init__.py
│   ├── task_controller.py     # Toda regra de negócio e persistência de tasks (extraída de task_routes)
│   ├── user_controller.py     # Toda regra de negócio, autenticação e listagem de users
│   ├── category_controller.py # CRUD de categorias separado de relatórios
│   └── report_controller.py   # Agregações otimizadas de relatórios
├── routes/                    # Camada View/Routes enxuta (apenas HTTP request/response)
│   ├── __init__.py
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── category_routes.py     # Separado de report_routes.py
│   └── report_routes.py
├── middlewares/
│   ├── __init__.py
│   └── error_handler.py       # Error handlers globais registrados no Flask app
├── services/
│   └── notification_service.py # Sem credenciais hardcoded (lendo de config/settings.py)
├── utils/
│   └── helpers.py             # Funções utilitárias limpas, sem código morto ou bare except
├── database.py
├── seed.py
└── app.py                     # Composition root
```

---

## 4. Checklist de Conformidade Pós-Refatoração (Fase 3)

Antes de declarar a Fase 3 concluída, valide cada item abaixo:
1. [ ] **Estrutura MVC completa**: Diretórios `config/`, `models/`, `controllers/`, `views/` (ou `routes/`) e `middlewares/` criados e populados.
2. [ ] **Zero segredos hardcoded**: `SECRET_KEY`, senhas de banco, chaves de gateway e senhas SMTP extraídos para `config/` via variáveis de ambiente.
3. [ ] **Zero vazamento de dados sensíveis**: Endpoints `/health`, `/usuarios`, `/users` e `/login` não expõem `secret_key` nem hashes de senha (`password`), e logs não imprimem cartões de crédito.
4. [ ] **Zero SQL Injection**: Todas as queries utilizam placeholders `?` ou filtros parametrizados de ORM.
5. [ ] **Zero N+1 Queries**: Listagens de pedidos, relatórios financeiros, listagens de tasks e resumos utilizam `JOIN` ou pré-carregamento em lote.
6. [ ] **Zero APIs Deprecated**: `Model.query.get()` substituído por `db.session.get(Model, id)` e `datetime.utcnow()` substituído por helper UTC timezone-aware.
7. [ ] **Contratos HTTP intactos**: A aplicação sobe sem erros e todos os endpoints originais respondem nos mesmos caminhos e formatos esperados.
