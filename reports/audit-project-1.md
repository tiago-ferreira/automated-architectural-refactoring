================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1, sqlite3 (stdlib)
Domain:        E-commerce API (produtos, pedidos, itens_pedido, usuarios e relatórios de vendas)
Architecture:  Monolítica — tudo em 4 arquivos na raiz (app.py, controllers.py, models.py, database.py), sem separação real de camadas por domínio
Source files:  4 files analyzed (778 lines of code)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~778 lines of code

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] SQL Injection & Arbitrary SQL Execution Endpoint
File: models.py:28, models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-299, app.py:59-79
Description: Todas as queries em `models.py` concatenam parâmetros diretamente na string SQL usando o operador `+` (ex.: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` em `models.py:110` e `buscar_produtos` em `models.py:289-299`). Além disso, a rota `POST /admin/query` (`app.py:59-79`) executa qualquer instrução SQL enviada no corpo JSON (`cursor.execute(query)`) sem autenticação ou restrição.
Impact: Permite bypass completo de autenticação, leitura de dados sensíveis e destruição total do banco de dados via SQL Injection.
Recommendation: Substituir todas as queries concatenadas por queries parametrizadas com placeholders `?` (`cursor.execute(sql, params)`) nos Models e restringir/sanitizar operações administrativas.

### [CRITICAL] Hardcoded Credentials & Secret Exposure in Health Endpoint
File: app.py:7-8, controllers.py:288-289
Description: A chave secreta da aplicação está hardcoded no código-fonte (`app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` em `app.py:7`) com `DEBUG = True` (`app.py:8`), e essa mesma `secret_key` é retornada publicamente no payload JSON do endpoint `GET /health` (`controllers.py:289`).
Impact: Exposição pública da chave criptográfica do servidor, permitindo falsificação de sessões e comprometimento do ambiente.
Recommendation: Extrair `SECRET_KEY`, `DEBUG` e `DB_PATH` para `config/settings.py` lendo de variáveis de ambiente (`os.environ.get`) e remover imediatamente `secret_key` do retorno de `/health`.

### [CRITICAL] God Module / Monolithic Domain Mixing
File: models.py:1-314, controllers.py:1-292
Description: `models.py` concentra acesso a dados, cálculo de pedidos, baixa de estoque e regras de desconto de relatórios de 4 domínios distintos (`produtos`, `usuarios`, `pedidos`, `relatorios`) em um único arquivo procedural. Da mesma forma, `controllers.py` mistura todos os 14 handlers HTTP de todos os domínios em um único módulo.
Impact: Viola severamente o Single Responsibility Principle (SRP), gera alto acoplamento e impede testes unitários e manutenção isolada por domínio.
Recommendation: Decompor `models.py` e `controllers.py` em módulos coesos por domínio dentro dos pacotes `models/` (`produto_model.py`, `usuario_model.py`, `pedido_model.py`), `controllers/` (`produto_controller.py`, `usuario_controller.py`, `pedido_controller.py`) e `views/routes.py`.

### [CRITICAL] Plaintext Passwords Storage and Exposure in User Endpoints
File: database.py:75-83, models.py:79-86, models.py:95-102, models.py:109-111, models.py:126-129
Description: As senhas dos usuários são armazenadas em texto puro no banco (`admin123`, `123456`, `senha123` em `database.py:76-78` e `criar_usuario` em `models.py:126-129`) e são retornadas abertamente nos JSONs de `GET /usuarios` (`models.py:83`) e `GET /usuarios/<id>` (`models.py:99`).
Impact: Vazamento direto de credenciais de todos os usuários e administradores através da API de listagem/consulta.
Recommendation: Utilizar hashing seguro (`werkzeug.security.generate_password_hash` / `check_password_hash` com fallback compatível para os seeds legados) e omitir o campo `senha` na serialização pública de usuários.

### [HIGH] Architectural Layer Violation (Direct SQL in Entry Point & Controller)
File: app.py:47-79, controllers.py:264-292
Description: O arquivo de entrada `app.py` executa instruções `DELETE` e queries arbitrárias diretamente no banco de dados nas rotas `/admin/reset-db` (`app.py:47-57`) e `/admin/query` (`app.py:59-79`). Igualmente, `health_check()` em `controllers.py:266-274` abre cursores SQL e executa `SELECT COUNT(*)` diretamente, ignorando a camada de Model.
Impact: Quebra o encapsulamento da camada de persistência no padrão MVC, espalhando SQL por todas as camadas da aplicação.
Recommendation: Mover todas as operações de banco de dados de `/health` e `/admin/*` para a camada de Models/Database e orquestrá-las via Controllers, deixando `app.py` exclusivamente como Composition Root e `views/routes.py` apenas com o mapeamento de rotas.

### [HIGH] Mutable Global Database Connection (`check_same_thread=False`)
File: database.py:4-11
Description: `database.py` armazena uma única conexão SQLite na variável global mutável `db_connection` criada com `check_same_thread=False` (`database.py:10`) e compartilhada entre todas as threads/requisições sem fechamento ao final do ciclo de vida do request.
Impact: Risco de condições de corrida (race conditions), cursores concorrentes corrompendo transações e vazamento de recursos.
Recommendation: Gerenciar a conexão SQLite por escopo de requisição usando `flask.g` e `app.teardown_appcontext` em `config/settings.py`.

### [HIGH] Lack of Atomic Transaction Control & Coupled Side-Effects in Order Creation
File: models.py:133-169, controllers.py:208-210, controllers.py:247-250
Description: `criar_pedido` (`models.py:133-169`) insere o pedido, itera inserindo itens e atualiza o estoque sem bloco `try/except` com `db.rollback()` em caso de falha intermediária. Além disso, `controllers.py` mistura responsabilidades de notificação (email/SMS/push simulados via `print` nas linhas 208-210 e 247-250) diretamente no controller HTTP.
Impact: Uma falha no meio da gravação dos itens pode deixar o banco inconsistente, e o acoplamento de efeitos colaterais dificulta a evolução do fluxo de pedidos.
Recommendation: Garantir atomicidade transacional (`try ... commit` / `except ... rollback`) no `pedido_model.py` e isolar a lógica de negócio no `pedido_controller.py`.

### [MEDIUM] Nested N+1 Queries Problem in Order Listings
File: models.py:139-166, models.py:171-201, models.py:203-233
Description: Em `get_pedidos_usuario` (`models.py:171-201`) e `get_todos_pedidos` (`models.py:203-233`), para cada pedido retornado é executada 1 query em `itens_pedido` (`models.py:188, 220`) e, para cada item, mais 1 query em `produtos` (`models.py:192, 224`) para buscar o nome do produto. Em `criar_pedido` (`models.py:139-166`), cada produto também é consultado duas vezes em loops separados.
Impact: Crescimento quadrático/linear de queries ($1 + N + N \times M$ consultas ao SQLite por requisição), degradando severamente o tempo de resposta.
Recommendation: Eliminar o N+1 utilizando `LEFT JOIN` entre `itens_pedido` e `produtos` e reaproveitando os dados validados dos produtos durante a criação do pedido.

### [MEDIUM] Missing Centralized Error Handling & Code Duplication
File: controllers.py:5-292, models.py:171-233
Description: Todos os 14 handlers de `controllers.py` duplicam blocos `try ... except Exception as e: return jsonify({"erro": str(e)}), 500`, expondo mensagens de erro internas aos clientes. Além disso, `get_pedidos_usuario` (`models.py:171-201`) e `get_todos_pedidos` (`models.py:203-233`) possuem 25 linhas de código idênticas para montagem dos itens do pedido.
Impact: Violação do princípio DRY (Don't Repeat Yourself), manutenção custosa e vazamento de detalhes internos de infraestrutura em respostas HTTP 500.
Recommendation: Criar `middlewares/error_handler.py` para registrar tratadores centralizados de erro no Flask e extrair um helper compartilhado em `models/pedido_model.py` para carregar itens com `JOIN`.

### [LOW] Magic Numbers in Sales Report & Hardcoded Validation Constants
File: models.py:257-262, controllers.py:47-53, controllers.py:242
Description: Valores numéricos mágicos de faixas de faturamento (`10000`, `5000`, `1000`) e alíquotas de desconto (`0.1`, `0.05`, `0.02`) estão soltos em `relatorio_vendas()` (`models.py:257-262`), assim como limites de tamanho de nome (`2`, `200`), categorias válidas (`controllers.py:52`) e status de pedidos (`controllers.py:242`).
Impact: Reduz a legibilidade e exige edição direta nos algoritmos caso as regras comerciais mudem.
Recommendation: Extrair todas as constantes de negócio (`DISCOUNT_TIERS`, `VALID_CATEGORIES`, `VALID_ORDER_STATUSES`, `MIN_NAME_LEN`, `MAX_NAME_LEN`) para `config/settings.py`.

### [LOW] Ad-hoc `print()` Statements Instead of Structured Logging
File: app.py:56, app.py:83-86, controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208-210, controllers.py:219, controllers.py:248, controllers.py:250
Description: Uso generalizado de `print("..." + str(var))` para registrar eventos operacionais e erros ao longo de `app.py` e `controllers.py`.
Impact: Logs sem timestamp, nível de severidade (`INFO`, `WARNING`, `ERROR`) ou controle de destino em produção.
Recommendation: Substituir chamadas `print()` pelo módulo padrão `logging` configurado na aplicação.

### [LOW] Unused Imports and Shadowed Built-ins (`id`)
File: database.py:2, models.py:2, models.py:24, models.py:54, models.py:65, models.py:89, controllers.py:14, controllers.py:56, controllers.py:64, controllers.py:98, controllers.py:136, controllers.py:160
Description: `import os` em `database.py:2` e `import sqlite3` em `models.py:2` não são utilizados; além disso, diversas funções usam o nome `id` como parâmetro/variável local, sombreando a função built-in `id()` do Python.
Impact: Poluição de escopo e alertas de linter (PEP 8).
Recommendation: Remover imports não utilizados e renomear variáveis/parâmetros locais para `produto_id` / `usuario_id` onde aplicável (mantendo a compatibilidade das rotas Flask).

================================
Total: 12 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
