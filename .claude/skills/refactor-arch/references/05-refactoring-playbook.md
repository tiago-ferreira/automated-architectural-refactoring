# 05 — Playbook de Refatoração com Exemplos Antes/Depois (Fase 3)

Este playbook fornece **11 padrões concretos de transformação de código** (com exemplos Antes e Depois em Python/Flask e Node.js/Express) mapeados diretamente para o catálogo de anti-patterns (`02-anti-patterns-catalog.md`).

> **Regra de fechamento de findings em endpoints administrativos (obrigatória)**: sempre que um finding da Fase 2 citar uma rota administrativa, de debug ou de manutenção (ex.: `/admin/query`, `/admin/reset-db`, `/debug/*`, `/internal/*`, consoles SQL, rotas de seed/reset), o finding **só é considerado fechado** quando a rota for **removida** ou **protegida por autenticação + autorização fail-closed** conforme o **Padrão 11**. Restringir o payload (ex.: aceitar apenas `SELECT`, bloquear `;`, blacklist de palavras-chave) **não fecha** o finding — a rota continua aberta a qualquer pessoa.

---

## Padrão 1: Eliminação de SQL Injection via Queries Parametrizadas (`CRITICAL`)

### Antes (Vulnerável — Concatenação de Strings)
```python
# models.py
def login_usuario(email, senha):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
    )
    return cursor.fetchone()

def buscar_produtos(termo, categoria=None):
    query = "SELECT * FROM produtos WHERE 1=1"
    if termo:
        query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"
    if categoria:
        query += " AND categoria = '" + categoria + "'"
    cursor.execute(query)
```

### Depois (Seguro — Placeholders `?` e Tupla de Parâmetros)
```python
# models/usuario_model.py
def buscar_por_email(email: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, email, senha, tipo, criado_em FROM usuarios WHERE email = ?", (email,))
    return cursor.fetchone()

# models/produto_model.py
def buscar_produtos(termo: str = "", categoria: str = None, preco_min: float = None, preco_max: float = None):
    db = get_db()
    cursor = db.cursor()
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        like_term = f"%{termo}%"
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend([like_term, like_term])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)
    cursor.execute(query, tuple(params))
    return [dict(row) for row in cursor.fetchall()]
```

> **Atenção**: queries parametrizadas resolvem a concatenação de entrada em SQL fixo. **Não** se aplicam a endpoints que recebem a instrução SQL inteira no payload (ex.: `POST /admin/query` com `{"sql": "..."}`) — para esses, aplique obrigatoriamente o **Padrão 11** (remover a rota). Um "modo somente `SELECT`" ainda permite ler qualquer tabela, inclusive `usuarios.senha`.

---

## Padrão 2: Extração de Credenciais Hardcoded e Remoção de Vazamentos (`CRITICAL`)

### Antes (Inseguro — Segredos no Código, Logs e Respostas HTTP)
```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"

# controllers.py (/health)
return jsonify({
    "status": "ok",
    "secret_key": "minha-chave-super-secreta-123"
}), 200
```
```javascript
// src/utils.js & src/AppManager.js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef" };
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

### Depois (Seguro — Módulo `config/settings` e Mascaramento)
```python
# config/settings.py
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-secret-key-change-in-prod")
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1")
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    ENVIRONMENT = os.environ.get("APP_ENV", "development")

# controllers/sistema_controller.py (/health sem vazar secret_key)
return {
    "status": "ok",
    "database": "connected",
    "counts": counts,
    "versao": "1.0.0",
    "ambiente": Config.ENVIRONMENT,
    "db_path": Config.DB_PATH,
    "debug": Config.DEBUG
}
```
```javascript
// src/config/settings.js
const settings = {
    port: Number(process.env.PORT) || 3000,
    dbUser: process.env.DB_USER || "admin_master",
    dbPass: process.env.DB_PASS || "",
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "pk_test_configured_via_env",
    smtpUser: process.env.SMTP_USER || "no-reply@fullcycle.com.br"
};
// No checkoutController.js: nunca logar número completo do cartão nem a chave privada!
const maskedCard = `****-****-****-${ String(cardNumber).slice(-4) }`;
```

---

## Padrão 3: Hash Seguro de Senhas e Ocultação em Serializações (`CRITICAL`)

### Antes (Inseguro — MD5 sem Salt / Base64 Fake / Vazamento em `to_dict()`)
```python
# models/user.py
def to_dict(self):
    return {'id': self.id, 'name': self.name, 'email': self.email, 'password': self.password}

def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()
```
```javascript
// src/utils.js
function badCrypto(pwd) {
    let hash = "";
    for (let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

### Depois (Seguro — Werkzeug PBKDF2/Scrypt e `crypto.scryptSync` + DTO Limpo)
```python
# models/user.py
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    # ...
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, pwd: str):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd: str) -> bool:
        return check_password_hash(self.password, pwd)
```
```javascript
// src/config/security.js
const crypto = require('crypto');

function hashPassword(password) {
    const salt = crypto.randomBytes(16).toString('hex');
    const derived = crypto.scryptSync(String(password), salt, 32).toString('hex');
    return `${salt}:${derived}`;
}
```

---

## Padrão 4: Decomposição de God Class / God Module em Camadas MVC (`CRITICAL`)

### Antes (God Class Monolítica — `AppManager.js`)
```javascript
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }
    initDb() { /* CREATE TABLE + INSERTs */ }
    setupRoutes(app) {
        app.post('/api/checkout', (req, res) => { /* validação + SQL + regra de cartão + cache */ });
        app.get('/api/admin/financial-report', (req, res) => { /* loops N+1 de SQL */ });
        app.delete('/api/users/:id', (req, res) => { /* DELETE direto */ });
    }
}
```

### Depois (Separação MVC: Model + Controller + View/Routes)
```javascript
// src/models/courseModel.js
class CourseModel {
    constructor(db) { this.db = db; }
    findActiveById(courseId) {
        return this.db.get("SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1", [courseId]);
    }
}

// src/controllers/checkoutController.js
class CheckoutController {
    constructor({ courseModel, userModel, enrollmentModel, auditService }) {
        this.courseModel = courseModel;
        this.userModel = userModel;
        this.enrollmentModel = enrollmentModel;
        this.auditService = auditService;
    }

    async checkout(req, res, next) {
        try {
            const { usr: userName, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body || {};
            if (!userName || !email || !courseId || !cardNumber) {
                return res.status(400).send("Bad Request");
            }
            const course = await this.courseModel.findActiveById(courseId);
            if (!course) {
                return res.status(404).send("Curso não encontrado");
            }
            // ... orquestração limpa ...
        } catch (err) {
            next(err);
        }
    }
}

// src/views/routes.js
const express = require('express');
function createRoutes({ checkoutController, reportController, userController }) {
    const router = express.Router();
    router.post('/api/checkout', (req, res, next) => checkoutController.checkout(req, res, next));
    router.get('/api/admin/financial-report', (req, res, next) => reportController.getFinancialReport(req, res, next));
    router.delete('/api/users/:id', (req, res, next) => userController.deleteUser(req, res, next));
    return router;
}
```

---

## Padrão 5: Extração de Fat Routes para Controllers Dedicados (`HIGH`)

### Antes (Fat Route acessando `db.session` e fazendo regras de negócio)
```python
# routes/task_routes.py
@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deletada com sucesso'}), 200
    except:
        db.session.rollback()
        return jsonify({'error': 'Erro ao deletar'}), 500
```

### Depois (Route enxuta na View + Lógica no Controller)
```python
# controllers/task_controller.py
class TaskController:
    @staticmethod
    def delete_task(task_id: int):
        task = db.session.get(Task, task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404
        try:
            db.session.delete(task)
            db.session.commit()
            return {'message': 'Task deletada com sucesso'}, 200
        except Exception:
            db.session.rollback()
            return {'error': 'Erro ao deletar'}, 500

# routes/task_routes.py
@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    body, status = TaskController.delete_task(task_id)
    return jsonify(body), status
```

---

## Padrão 6: Substituição de Callback Hell por Async/Await e Transações (`HIGH`)

### Antes (6 níveis de Callbacks sem Transação e Deleção Suja)
```javascript
// src/AppManager.js
app.delete('/api/users/:id', (req, res) => {
    let id = req.params.id;
    this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
        res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
    });
});
```

### Depois (Async/Await Promisificado + Limpeza Transacional em Cascata)
```javascript
// src/models/userModel.js
async deleteWithDependencies(userId) {
    await this.db.run("BEGIN TRANSACTION");
    try {
        await this.db.run(
            "DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)",
            [userId]
        );
        await this.db.run("DELETE FROM enrollments WHERE user_id = ?", [userId]);
        await this.db.run("DELETE FROM users WHERE id = ?", [userId]);
        await this.db.run("COMMIT");
    } catch (error) {
        await this.db.run("ROLLBACK");
        throw error;
    }
}
```

---

## Padrão 7: Eliminação de Estado Global Mutável e Conexão Thread-Unsafe (`HIGH`)

### Antes (Conexão SQLite Global Compartilhada entre Threads)
```python
# database.py
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```

### Depois (Conexão Gerenciada por Contexto de Requisição `flask.g` com Fallback Seguro)
```python
# config/settings.py
import sqlite3
from flask import g, has_app_context

def get_db():
    if has_app_context():
        if "db" not in g:
            conn = sqlite3.connect(Config.DB_PATH)
            conn.row_factory = sqlite3.Row
            g.db = conn
        return g.db
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```

---

## Padrão 8: Eliminação de Queries N+1 com SQL `JOIN` e Eager Loading (`MEDIUM`)

### Antes (N+1 Queries em Loops Aninhados)
```python
# models.py (1 query para pedidos + N queries para itens + N*M queries para produtos)
cursor.execute("SELECT * FROM pedidos")
for row in cursor.fetchall():
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
```javascript
// AppManager.js (N+1 em /api/admin/financial-report)
this.db.all("SELECT * FROM courses", [], (err, courses) => {
    courses.forEach(c => {
        this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
            enrollments.forEach(enr => {
                this.db.get("SELECT name, email FROM users WHERE id = ?", [enr.user_id], ...);
                this.db.get("SELECT amount, status FROM payments WHERE enrollment_id = ?", [enr.id], ...);
            });
        });
    });
});
```

### Depois (Single Query / Batch Query com `LEFT JOIN`)
```python
# models/pedido_model.py — Busca todos os itens e nomes de produtos em 1 único JOIN
cursor.execute("""
    SELECT ip.pedido_id, ip.produto_id, COALESCE(p.nome, 'Desconhecido') AS produto_nome,
           ip.quantidade, ip.preco_unitario
    FROM itens_pedido ip
    LEFT JOIN produtos p ON p.id = ip.produto_id
    WHERE ip.pedido_id = ?
""", (pedido_id,))
```
```javascript
// src/models/reportModel.js — 1 única query SQL com LEFT JOIN para o relatório financeiro
const rows = await this.db.all(`
    SELECT
        c.id AS course_id,
        c.title AS course_title,
        e.id AS enrollment_id,
        u.name AS student_name,
        p.amount AS payment_amount,
        p.status AS payment_status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u ON u.id = e.user_id
    LEFT JOIN payments p ON p.enrollment_id = e.id
    ORDER BY c.id, e.id
`);
```
```python
# controllers/task_controller.py (SQLAlchemy eager loading com joinedload)
from sqlalchemy.orm import joinedload
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
```

---

## Padrão 9: Atualização de APIs Deprecated (`Query.get` e `datetime.utcnow`) (`MEDIUM`)

### Antes (APIs Obsoletas do SQLAlchemy 1.x e Python <3.12)
```python
from datetime import datetime
task = Task.query.get(task_id)
if task.due_date and task.due_date < datetime.utcnow():
    ...
```

### Depois (SQLAlchemy 2.0 `db.session.get` e Helper UTC Timezone-Aware)
```python
# config/settings.py
from datetime import datetime, timezone

def utc_now_naive() -> datetime:
    """Retorna o horário UTC atual usando a API moderna timezone-aware (Python 3.12+) normalizado para comparação no SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

# controllers/task_controller.py
task = db.session.get(Task, task_id)
if task and task.is_overdue():
    ...
```

---

## Padrão 10: Centralização de Error Handling e Remoção de Bare `except:` (`MEDIUM` / `LOW`)

### Antes (`except:` Genérico e Try/Except Repetido)
```python
try:
    task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
except:
    return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
```

### Depois (Exceções Específicas + Middleware Global `error_handler`)
```python
# middlewares/error_handler.py
from flask import jsonify
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        return jsonify({"erro": exc.description, "error": exc.description, "sucesso": False}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc):
        return jsonify({"erro": "Erro interno do servidor", "error": "Erro interno", "sucesso": False}), 500

# Tratamento específico de ValueError na validação de data:
try:
    task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
except (ValueError, TypeError):
    return {'error': 'Formato de data inválido. Use YYYY-MM-DD'}, 400
```

---

## Padrão 11: Remoção ou Proteção de Endpoints Administrativos Perigosos (`CRITICAL`)

Aplica-se a qualquer rota que execute operações privilegiadas sem passar pela autorização normal do domínio: consoles SQL, reset/seed de banco, dumps, flags de debug, rotas `/admin/*`, `/internal/*` e `/debug/*`.

### Árvore de decisão (obrigatória na Fase 3)

| Tipo de endpoint | Ação obrigatória | Justificativa |
|---|---|---|
| Executa SQL / código / comando enviado pelo cliente (ex.: `POST /admin/query` com `{"sql": ...}`) | **REMOVER** a rota, o handler do Controller e a função do Model | Não existe allowlist segura para SQL arbitrário: `SELECT` sozinho já lê qualquer tabela (`usuarios`, hashes de senha, tokens). Nenhum cliente de negócio depende desse contrato. |
| Operação destrutiva ou de manutenção (ex.: `POST /admin/reset-db`, seed, purge) | **PROTEGER** com autenticação + autorização fail-closed (ou remover, se não houver uso legítimo) | A operação tem uso operacional legítimo, mas nunca pode ser anônima. |
| Leitura administrativa com payload fixo (ex.: `GET /api/admin/financial-report`) | **PROTEGER** com autenticação + autorização de papel `admin` | Expõe dados agregados sensíveis. |

### Requisitos da proteção (quando a rota for mantida)

1. **Fail-closed**: se a credencial administrativa não estiver configurada no ambiente (ex.: `ADMIN_API_TOKEN` vazio), a rota fica **desabilitada** e responde `404`/`403` — nunca cai para "liberado".
2. **Credencial fora do código**: lida de variável de ambiente via `config/settings` (Padrão 2). Nunca use fallback hardcoded para o token admin.
3. **Comparação em tempo constante**: `hmac.compare_digest` (Python) / `crypto.timingSafeEqual` (Node.js).
4. **Aplicada na camada de borda**: decorator/middleware em `middlewares/` aplicado no registro da rota (`views/`/`routes/`), não um `if` esquecível dentro do Controller.
5. Se o projeto já possuir autenticação real (sessão/JWT com papel `admin`), reutilize-a e exija o papel `admin` em vez de criar um token paralelo.

### Antes (Inseguro — "corrigido" apenas com restrição de payload)
```python
# views/routes.py
api_bp.add_url_rule("/admin/reset-db", "reset_database", pedido_controller.reset_database, methods=["POST"])
api_bp.add_url_rule("/admin/query", "executar_query", pedido_controller.executar_query, methods=["POST"])

# models/pedido_model.py
def executar_query_segura(query: str):
    cleaned = query.strip()
    if not cleaned.upper().startswith("SELECT"):   # ainda permite: SELECT email, senha FROM usuarios
        raise PermissionError("Apenas consultas SELECT de leitura são permitidas")
    cursor.execute(cleaned)
```

### Depois (Seguro — console SQL removido, manutenção protegida fail-closed)
```python
# config/settings.py
class Config:
    # Vazio por padrão: rotas administrativas ficam desabilitadas até o operador configurar o token.
    ADMIN_API_TOKEN = os.environ.get("ADMIN_API_TOKEN", "")
    ADMIN_TOKEN_HEADER = "X-Admin-Token"

# middlewares/admin_auth.py
import hmac
from functools import wraps
from flask import abort, request
from config.settings import Config, logger

def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not Config.ADMIN_API_TOKEN:
            abort(404)  # fail-closed: rota inexistente enquanto o token não estiver configurado
        provided = request.headers.get(Config.ADMIN_TOKEN_HEADER, "")
        if not hmac.compare_digest(provided.encode(), Config.ADMIN_API_TOKEN.encode()):
            logger.warning("Acesso administrativo negado em %s", request.path)
            abort(401)
        return view(*args, **kwargs)
    return wrapper

# views/routes.py  (/admin/query REMOVIDA: rota, controller e executar_query_segura apagados)
api_bp.add_url_rule(
    "/admin/reset-db", "reset_database",
    require_admin_token(pedido_controller.reset_database), methods=["POST"],
)
```
```javascript
// src/middlewares/adminAuth.js
const crypto = require('crypto');
const settings = require('../config/settings');

function requireAdminToken(req, res, next) {
    if (!settings.adminApiToken) return res.status(404).send('Not Found'); // fail-closed
    const provided = Buffer.from(String(req.get('X-Admin-Token') || ''));
    const expected = Buffer.from(settings.adminApiToken);
    if (provided.length !== expected.length || !crypto.timingSafeEqual(provided, expected)) {
        return res.status(401).send('Unauthorized');
    }
    return next();
}

// src/views/routes.js
router.get('/api/admin/financial-report', requireAdminToken, (req, res, next) => reportController.getFinancialReport(req, res, next));
```

### Validação obrigatória na Fase 3 (testes negativos)

O item `Zero anti-patterns remaining` só pode ser marcado se, para **cada** endpoint administrativo citado na Fase 2:

- **Rota removida** → requisição retorna `404`/`405` e não há mais referência ao handler/função no código (`grep` pelo nome do endpoint e da função do Model).
- **Rota protegida** →
  1. sem credencial → `401`/`403` (ou `404` se o token não estiver configurado) **e** nenhum efeito colateral (ex.: contagens do `/health` inalteradas após `POST /admin/reset-db`);
  2. credencial errada → `401`/`403`;
  3. credencial correta → status e payload originais preservados.
- Uma tentativa de ler a tabela de usuários (ex.: `{"sql": "SELECT email, senha FROM usuarios"}`) **não** retorna dados em nenhuma rota.

> **Contrato HTTP**: a remoção ou exigência de credencial nesses endpoints é uma exceção explícita à regra de preservação de contratos da skill. Liste no resumo da Fase 3 cada rota removida/protegida, o novo status sem credencial e a variável de ambiente necessária para operá-la.
