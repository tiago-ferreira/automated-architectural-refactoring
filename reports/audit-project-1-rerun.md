================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1, werkzeug (security), sqlite3 (stdlib), logging (stdlib)
Domain:        E-commerce API (produtos, pedidos, itens_pedido, usuarios e relatórios de vendas)
Architecture:  MVC já aplicado (config/, models/, controllers/, views/, middlewares/, app.py como Composition Root), porém com operações administrativas/de sistema alojadas no domínio de pedidos e config/settings.py acumulando conexão, schema e seed
Source files:  16 files analyzed (1099 lines of code) — inclui 6 arquivos __init__.py/shim (nenhum vazio)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   16 analyzed | ~1099 lines of code

## Summary
CRITICAL: 2 | HIGH: 5 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] Unauthenticated Arbitrary SQL Console (`POST /admin/query`)
File: views/routes.py:36, controllers/pedido_controller.py:111-123, models/pedido_model.py:224-236
Description: A Fase 3 anterior apenas restringiu o payload em `executar_query_segura` (`models/pedido_model.py:224-236`) a instruções que começam com `SELECT` e sem `;`. A rota continua registrada sem qualquer autenticação (`views/routes.py:36`) e executa o SQL enviado pelo cliente (`cursor.execute(cleaned)`). Verificado em runtime: `POST /admin/query {"sql": "SELECT id, email, senha, tipo FROM usuarios"}` sem credencial retorna `200` com e-mail, papel e hash scrypt da senha de todos os usuários, incluindo o admin.
Impact: Qualquer pessoa anônima lê qualquer tabela do banco (usuários, hashes de senha, pedidos), permitindo ataques offline de quebra de hash e enumeração completa de dados pessoais.
Recommendation: Aplicar o Padrão 11 do playbook (SQL enviado pelo cliente → REMOVER): apagar a rota de `views/routes.py`, o handler `executar_query` (e seu export em `controllers/__init__.py`) e `executar_query_segura` (e seu export em `models/__init__.py`). Validar que `POST /admin/query` responde `404`/`405`.

### [CRITICAL] Unauthenticated Destructive Admin Endpoint (`POST /admin/reset-db`)
File: views/routes.py:35, controllers/pedido_controller.py:105-108, models/pedido_model.py:210-221
Description: `POST /admin/reset-db` está registrada sem autenticação e executa `DELETE FROM itens_pedido/pedidos/produtos/usuarios` (`models/pedido_model.py:214-217`). Verificado em runtime: a chamada anônima retorna `200 {"mensagem": "Banco de dados resetado"}` e apaga todos os dados.
Impact: Qualquer cliente anônimo destrói o banco inteiro com uma única requisição (negação de serviço e perda total de dados).
Recommendation: Aplicar o Padrão 11 (operação de manutenção → PROTEGER fail-closed): criar `middlewares/admin_auth.py` com `require_admin_token` (header `X-Admin-Token`, comparação via `hmac.compare_digest`, token lido de `ADMIN_API_TOKEN` em `config/settings.py`, rota desabilitada com `404` quando o token não estiver configurado) e aplicá-lo no registro da rota em `views/routes.py`.

### [HIGH] Missing Order Item Validation Corrupts Stock and Totals
File: controllers/pedido_controller.py:8-23, models/pedido_model.py:13-34, models/pedido_model.py:56-59
Description: `criar_pedido` não valida `usuario_id` (existência) nem `quantidade` (tipo/positividade) e acessa `item["produto_id"]`/`item["quantidade"]` sem checagem. Verificado em runtime: `{"usuario_id": 999, "itens": [{"produto_id": 1, "quantidade": -5}]}` cria o pedido com `total = -29999.95` e **aumenta** o estoque do produto de 10 para 15; um item sem `produto_id` gera `500` (`KeyError`). Além disso, a checagem de estoque (`models/pedido_model.py:23`) ocorre fora da transação e o `UPDATE` (`models/pedido_model.py:56-59`) não usa `WHERE estoque >= ?`, permitindo overselling concorrente.
Impact: Manipulação de estoque e faturamento por qualquer cliente, pedidos órfãos para usuários inexistentes e erros 500 em entradas malformadas.
Recommendation: Validar no `pedido_controller` que cada item tem `produto_id` e `quantidade` inteiros positivos e que o usuário existe (via `usuario_model`), e tornar a baixa de estoque condicional (`UPDATE ... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?` verificando `rowcount`) dentro da mesma transação.

### [HIGH] Missing Authentication/Authorization on Business Routes
File: views/routes.py:12-30, controllers/usuario_controller.py:37-54
Description: `POST /login` só devolve os dados do usuário, sem emitir token ou sessão (`controllers/usuario_controller.py:48-51`). Consequentemente nenhuma rota de negócio exige identidade: `GET /usuarios` lista e-mails de todos os usuários, `GET /pedidos` lista todos os pedidos, `PUT /pedidos/<id>/status`, `POST/PUT/DELETE /produtos` e `GET /relatorios/vendas` (faturamento) são anônimos.
Impact: Qualquer pessoa altera catálogo e status de pedidos e acessa dados pessoais e financeiros.
Recommendation: Introduzir autenticação por token assinado (`itsdangerous` com `SECRET_KEY`) emitido em `/login` e um middleware de autorização por papel (`admin` para escrita de produtos, status de pedidos, relatórios e listagem de usuários). **Atenção**: essa mudança altera o contrato de todas as rotas de negócio e vai além do Padrão 11; recomenda-se aprovação explícita ou tratá-la como mudança separada.

### [HIGH] Plaintext Password Comparison Fallback
File: models/usuario_model.py:18-23
Description: `_verify_password` aceita senhas armazenadas em texto puro: se o valor salvo não começa com `scrypt:`/`pbkdf2:`, compara com `stored_password == provided_password` (comparação não constante) e nunca re-hasheia o registro após login bem-sucedido.
Impact: Bancos legados (`loja.db` pré-refatoração) mantêm senhas em texto puro indefinidamente, e a comparação direta é suscetível a timing attacks.
Recommendation: Migrar registros legados para hash (re-hash no primeiro login bem-sucedido ou script de migração no `init_db`) e, para o fallback restante, usar `hmac.compare_digest`; remover o fallback após a migração.

### [HIGH] System/Admin Operations Mixed into the Pedido Domain
File: controllers/pedido_controller.py:67-123, models/pedido_model.py:193-236, controllers/__init__.py:16-26, models/__init__.py:16-25
Description: `pedido_controller.py` contém `health_check`, `index`, `reset_database` e `executar_query`, e `pedido_model.py` contém `get_database_counts`, `reset_all_tables` e `executar_query_segura` — operações de sistema/administração que não pertencem ao domínio de pedidos.
Impact: Viola SRP; endpoints sensíveis ficam escondidos dentro de um módulo de negócio, dificultando revisão de segurança e aplicação de políticas de acesso por domínio.
Recommendation: Extrair `controllers/sistema_controller.py` (`health_check`, `index`, `reset_database`) e `models/sistema_model.py` (`get_database_counts`, `reset_all_tables`), atualizando os imports em `views/routes.py` e os barrels.

### [HIGH] Mutable Global Connection and DB Lifecycle Inside Config Module
File: config/settings.py:58-59, config/settings.py:62-185
Description: `config/settings.py` mantém estado global mutável (`_standalone_conn`, `_schema_initialized_for`) e uma conexão SQLite compartilhada fora do contexto Flask (`config/settings.py:166-169`), além de concentrar criação de schema, seed e ciclo de vida da conexão junto com as configurações e o setup de logging.
Impact: Conexão compartilhada nunca fechada fora do request; módulo de configuração com múltiplas responsabilidades, dificultando testes isolados.
Recommendation: Mover `get_db`/`close_db`/`init_db`/schema/seed para um módulo dedicado (`database.py` ou `config/database.py`), eliminar `_standalone_conn` abrindo conexões de curta duração fora do contexto da aplicação, e deixar `config/settings.py` apenas com `Config` e logging.

### [MEDIUM] Missing Input Validation and Silent Success Responses
File: controllers/produto_controller.py:20-28, controllers/pedido_controller.py:50-59, models/pedido_model.py:142-150, controllers/usuario_controller.py:20-34, models/usuario_model.py:62-73
Description: `_validar_payload_produto` compara `preco < 0` sem verificar o tipo — verificado: `{"preco": "x"}` gera `500` (`TypeError`). `PUT /pedidos/9999/status` retorna `200 "Status atualizado"` para pedido inexistente (o model ignora `rowcount`). `POST /usuarios` aceita e-mail duplicado (verificado com `admin@loja.com` → `201`).
Impact: Erros 500 para entradas inválidas, respostas enganosas e contas duplicadas que tornam o login ambíguo.
Recommendation: Validar tipos numéricos no controller (`400`), retornar `404` quando `rowcount == 0` em updates, e checar e-mail existente antes de inserir (`409`), idealmente com índice `UNIQUE` em `usuarios.email`.

### [MEDIUM] Schema DDL Executed on Every Request
File: config/settings.py:156-164, config/settings.py:68-121
Description: `get_db()` chama `_ensure_schema_and_seed` a cada nova conexão de request, executando 4 `CREATE TABLE IF NOT EXISTS` e um `commit` por requisição, embora `init_db()` já rode no boot (`app.py:19`).
Impact: Overhead e escrita desnecessária em todas as requisições, com risco de contenção de lock no SQLite.
Recommendation: Executar schema/seed apenas em `init_db()` no boot e deixar `get_db()` apenas abrir a conexão.

### [MEDIUM] Sensitive Configuration Exposure and Insecure Secret Fallback
File: controllers/pedido_controller.py:67-82, config/settings.py:18
Description: `GET /health` expõe publicamente `db_path` (caminho absoluto do arquivo do banco), flag `debug`, `ambiente` e contagem de usuários. `SECRET_KEY` usa fallback fixo `"dev-only-configured-via-env"` quando a variável de ambiente não existe.
Impact: Reconhecimento facilitado da infraestrutura e segredo previsível caso a chave passe a assinar tokens/sessões.
Recommendation: Restringir `/health` a `status`/`database`/`versao` (dados detalhados apenas em rota protegida) e falhar no boot em `APP_ENV=producao` sem `SECRET_KEY` definida.

### [LOW] Shadowed Built-in `id` Still Present
File: controllers/produto_controller.py:47, controllers/produto_controller.py:76, controllers/produto_controller.py:97, controllers/usuario_controller.py:13, views/routes.py:14, views/routes.py:16-17, views/routes.py:21
Description: A recomendação anterior de renomear `id` não foi aplicada: handlers ainda recebem `id` (sombreando o built-in) a partir de `<int:id>` nas rotas.
Impact: Alertas de linter e legibilidade reduzida.
Recommendation: Renomear para `<int:produto_id>` / `<int:usuario_id>` e os parâmetros correspondentes (o contrato de URL não muda).

### [LOW] Dead Code and Unused Re-exports
File: database.py:1-4, config/__init__.py:1-4, models/__init__.py:1-46, controllers/__init__.py:1-48, models/pedido_model.py:196, models/pedido_model.py:150, models/produto_model.py:71, models/produto_model.py:79
Description: `database.py` não é importado por nenhum módulo; os barrels `models/__init__.py` e `controllers/__init__.py` re-exportam funções que ninguém consome (os chamadores importam os submódulos); `cursor.execute("SELECT 1")` em `get_database_counts` é redundante; funções de escrita retornam `True` constante, ignorado pelos chamadores.
Impact: Ruído e superfície de manutenção desnecessária (ex.: `executar_query_segura` continua exportada mesmo se a rota for removida).
Recommendation: Remover `database.py` (ou torná-lo o módulo real de DB, ver finding de config), enxugar os barrels, remover o `SELECT 1` e os retornos constantes.

### [LOW] Hardcoded Status Strings in Sales Report SQL
File: models/pedido_model.py:162-164
Description: `relatorio_vendas` usa literais `'pendente'`, `'aprovado'`, `'cancelado'` no SQL, enquanto os status oficiais estão em `Config.VALID_ORDER_STATUSES`.
Impact: Divergência silenciosa se os status mudarem.
Recommendation: Parametrizar os status no SQL (`SUM(CASE WHEN status = ? ...)`) usando constantes de `Config`.

================================
Total: 13 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
