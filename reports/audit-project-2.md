================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js)
Framework:     Express 4.18.2
Dependencies:  express ^4.18.2, sqlite3 ^5.1.6
Domain:        LMS / Course E-commerce API (cursos, matrículas, usuários, checkout/pagamentos e relatório financeiro)
Architecture:  Monolítica centrada em God Class (AppManager) — banco de dados, rotas, regras de negócio e relatórios acoplados em 3 arquivos (src/app.js, src/AppManager.js, src/utils.js)
Source files:  3 files analyzed (180 lines of code)
DB tables:     users, courses, enrollments, payments, audit_logs
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 2 | LOW: 2

## Findings

### [CRITICAL] God Class (`AppManager`) Violating MVC and Single Responsibility Principle
File: src/AppManager.js:4-139, src/app.js:8-10
Description: A classe `AppManager` centraliza todas as responsabilidades da aplicação: instancia o banco SQLite (`src/AppManager.js:7`), cria tabelas e executa seed (`src/AppManager.js:10-23`), define todas as rotas HTTP do Express (`src/AppManager.js:25-138`), processa pagamentos/matrículas e monta relatórios financeiros.
Impact: Acoplamento total entre infraestrutura de banco de dados, roteamento HTTP e lógica de domínio, tornando impossível testar ou dar manutenção isolada em qualquer camada.
Recommendation: Decompor `AppManager.js` seguindo o padrão MVC em `src/config/` (`settings.js`, `database.js`), `src/models/` (`courseModel.js`, `userModel.js`, `enrollmentModel.js`, `reportModel.js`), `src/controllers/` (`checkoutController.js`, `reportController.js`, `userController.js`), `src/views/routes.js` e `src/middlewares/errorHandler.js`.

### [CRITICAL] Hardcoded Production Secrets & Credit Card / Gateway Key Exposure in Logs
File: src/utils.js:1-7, src/AppManager.js:18, src/AppManager.js:45
Description: Credenciais críticas de produção estão hardcoded em `src/utils.js:1-7` (`dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`). Pior ainda, durante o checkout (`src/AppManager.js:45`), a aplicação imprime o número completo do cartão de crédito do cliente (`cc`) e a chave privada do gateway no console (`console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`).
Impact: Violação crítica de segurança e PCI-DSS, expondo dados de cartão de crédito em texto claro nos logs do servidor e vazando chaves de API no controle de versão.
Recommendation: Extrair todas as configurações para `src/config/settings.js` lendo de variáveis de ambiente (`process.env`) e remover/mascarar dados sensíveis de cartão e chaves em qualquer log.

### [CRITICAL] Broken Custom Cryptography (`badCrypto`) Blocking Event Loop
File: src/utils.js:17-23, src/AppManager.js:68
Description: A função `badCrypto(pwd)` (`src/utils.js:17-23`) não realiza hashing criptográfico: ela apenas converte a senha para Base64 (`Buffer.from(pwd).toString('base64')`), extrai os 2 primeiros caracteres e os concatena 10.000 vezes em um loop síncrono antes de truncar em 10 caracteres (`hash.substring(0, 10)`), além de usar `"123456"` como senha padrão caso `pwd` seja omitido (`src/AppManager.js:68`).
Impact: Qualquer senha com o mesmo prefixo de 2 bytes gera exatamente o mesmo "hash" (colisão trivial e reversível), além de bloquear a thread principal do Node.js a cada cadastro.
Recommendation: Substituir `badCrypto` por derivação criptográfica real usando o módulo nativo `crypto` (`crypto.scryptSync` com salt aleatório de 16 bytes) em `src/config/settings.js`.

### [HIGH] Callback Hell, Mixed `this`/`self` Context & Missing Database Transactions
File: src/AppManager.js:26-78
Description: O handler `POST /api/checkout` (`src/AppManager.js:28-78`) encadeia 6 níveis de callbacks aninhados misturando `this.db` e `self.db` para buscar curso, buscar/criar usuário, criar matrícula, registrar pagamento e gravar log de auditoria, sem utilizar transações SQL (`BEGIN TRANSACTION` / `COMMIT` / `ROLLBACK`).
Impact: Caso a inserção em `payments` ou `audit_logs` falhe, o usuário e a matrícula permanecem gravados de forma inconsistente (matrícula gratuita sem pagamento), além da altíssima complexidade ciclomática.
Recommendation: Criar um wrapper promisificado para o SQLite em `src/config/database.js` (`run`, `get`, `all`, `withTransaction`) e reescrever o fluxo no `CheckoutController` com `async/await` e controle transacional.

### [HIGH] Referential Integrity Violation on User Deletion (Orphaned Records)
File: src/AppManager.js:131-137
Description: A rota `DELETE /api/users/:id` executa apenas `DELETE FROM users WHERE id = ?` (`src/AppManager.js:133`) sem remover ou tratar os registros dependentes nas tabelas `enrollments` e `payments`, deixando dados órfãos que distorcem o relatório financeiro (`student: 'Unknown'`).
Impact: Corrupção da integridade referencial do banco de dados e inconsistência contábil nos relatórios administrativos.
Recommendation: Implementar exclusão transacional em cascata no `UserModel` (removendo pagamentos das matrículas do usuário, matrículas do usuário e o registro em `users` dentro de uma transação).

### [HIGH] Unbounded Mutable Global State (`globalCache` and `totalRevenue`) & Mixed Concerns
File: src/utils.js:9-15, src/AppManager.js:2, src/AppManager.js:59
Description: `src/utils.js` mantém variáveis globais mutáveis `globalCache = {}` e `totalRevenue = 0` (`src/utils.js:9-10`), e a função `logAndCache(key, data)` (`src/utils.js:12-15`) mistura logging no console com escrita em memória global sem limite de chaves ou TTL.
Impact: Vazamento de memória (memory leak) conforme novos checkouts ocorrem e acoplamento a estado global mutável que impede escalabilidade horizontal e testes determinísticos.
Recommendation: Encapsular o registro de eventos e cache em um utilitário/serviço com limite máximo de entradas (bounded LRU/FIFO) e responsabilidades separadas.

### [MEDIUM] Severe N+1 Query Problem & Fragile Manual Async Counters in Financial Report
File: src/AppManager.js:80-129
Description: A rota `GET /api/admin/financial-report` (`src/AppManager.js:80-129`) busca todos os cursos e, dentro de `courses.forEach`, executa 1 query em `enrollments` por curso (`linha 92`); dentro de `enrollments.forEach`, executa mais 2 queries (`SELECT ... FROM users` na `linha 104` e `SELECT ... FROM payments` na `linha 106`), coordenando o término manualmente via contadores `coursesPending` e `enrPending`.
Impact: Dispara $1 + C + 2 \times E$ queries ao banco para uma única chamada HTTP e trava a requisição infinitamente (timeout) se qualquer callback intermediário retornar erro.
Recommendation: Substituir todas as queries em loop por uma única consulta SQL agregada/relacional com `LEFT JOIN` entre `courses`, `enrollments`, `users` e `payments` no `ReportModel`.

### [MEDIUM] Missing Centralized Error Middleware & Unchecked Database Callback Errors
File: src/app.js:1-14, src/AppManager.js:57, src/AppManager.js:92, src/AppManager.js:104, src/AppManager.js:106, src/AppManager.js:133
Description: A aplicação Express não possui middleware global de tratamento de erros, e diversos callbacks do SQLite (`src/AppManager.js:57, 92, 104, 106, 133`) ignoram completamente o argumento `err`.
Impact: Erros de banco passam despercebidos ou derrubam o processo sem resposta HTTP padronizada.
Recommendation: Criar `src/middlewares/errorHandler.js` e encaminhar exceções assíncronas via `next(err)` nos Controllers.

### [LOW] Cryptic Single-Letter Variable Naming
File: src/AppManager.js:29-33, src/AppManager.js:52, src/AppManager.js:89, src/AppManager.js:102
Description: Uso de identificadores crípticos de 1 a 3 caracteres nas rotas e callbacks: `u`, `e`, `p`, `cid`, `cc` (`src/AppManager.js:29-33`), `enrId` (`linha 52`), `c` (`linha 89`) e `enr` (`linha 102`).
Impact: Prejudica a leitura imediata do domínio e aumenta o risco de confusão entre parâmetros durante manutenções.
Recommendation: Utilizar nomes descritivos (`userName`, `email`, `password`, `courseId`, `cardNumber`, `enrollmentId`, `course`, `enrollment`).

### [LOW] Magic Numbers and Hardcoded Business Literals
File: src/utils.js:6, src/utils.js:19-22, src/AppManager.js:46, src/AppManager.js:68
Description: Literais mágicos espalhados pelo código, como a porta `3000` (`src/utils.js:6`), iterações `10000`, `2`, `10` (`src/utils.js:19-22`), prefixo de aprovação de cartão `"4"` (`src/AppManager.js:46`) e senha default `"123456"` (`src/AppManager.js:68`).
Impact: Dificulta ajustes de configuração e obscurece o significado das constantes de negócio.
Recommendation: Centralizar constantes nomeadas (`APPROVED_CARD_PREFIX`, `PAYMENT_STATUS`, `DEFAULT_PORT`, `MAX_CACHE_ENTRIES`) em `src/config/settings.js`.

================================
Total: 10 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
