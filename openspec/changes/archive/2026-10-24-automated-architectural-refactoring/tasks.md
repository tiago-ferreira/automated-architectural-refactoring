# Tasks

## 1. Preparação do Repositório e Aquisição dos Projetos-Alvo

- [x] 1.1 Inicializar o repositório Git (se ainda não inicializado), clonar o repositório base `https://github.com/devfullcycle/mba-ia-refactor-projects-skill` e importar as pastas `code-smells-project/`, `ecommerce-api-legacy/` e `task-manager-api/` para a raiz do workspace, verificando com `ls -d code-smells-project ecommerce-api-legacy task-manager-api` que os 3 diretórios e seus arquivos-fonte originais estão presentes.
- [x] 1.2 Configurar os ambientes de execução dos 3 projetos (ambiente virtual Python para `code-smells-project` e `task-manager-api`, e `npm install` para `ecommerce-api-legacy`) e verificar que as dependências instalam sem erros e cada aplicação original sobe em modo de teste.
- [x] 1.3 Criar o diretório `reports/` na raiz do repositório e realizar um commit inicial com os projetos originais intactos para preservar o baseline de comparação antes/depois, verificando via `git status` e `git log -n 1`.

## 2. Análise Manual dos Três Projetos Legados

- [x] 2.1 Inspecionar manualmente o código-fonte de `code-smells-project/` (`app.py`, `controllers.py`, `models.py`, `database.py`), identificar no mínimo 5 problemas (incluindo >= 1 CRITICAL/HIGH, >= 2 MEDIUM, >= 2 LOW) com arquivo, linha exata e justificativa, e documentá-los na seção "Análise Manual" do `README.md`.
- [x] 2.2 Inspecionar manualmente o código-fonte de `ecommerce-api-legacy/` (`src/app.js`, `src/AppManager.js`, `src/utils.js`), identificar no mínimo 5 problemas (incluindo >= 1 CRITICAL/HIGH, >= 2 MEDIUM, >= 2 LOW) com arquivo, linha exata e justificativa, e documentá-los na seção "Análise Manual" do `README.md`.
- [x] 2.3 Inspecionar manualmente o código-fonte de `task-manager-api/` (`app.py`, `database.py`, `seed.py`, `models/`, `routes/`, `services/`, `utils/`), identificar no mínimo 5 problemas (incluindo >= 1 CRITICAL/HIGH, >= 2 MEDIUM, >= 2 LOW) com arquivo, linha exata e justificativa, e documentá-los na seção "Análise Manual" do `README.md`, verificando que o `README.md` contém os 3 blocos completos de análise manual.

## 3. Construção da Skill `refactor-arch` e Arquivos de Referência

- [x] 3.1 Criar o arquivo `code-smells-project/.claude/skills/refactor-arch/SKILL.md` com frontmatter YAML e instruções completas para as 3 fases sequenciais (Fase 1: Análise, Fase 2: Auditoria com pausa obrigatória para confirmação do usuário, Fase 3: Refatoração MVC e Validação), verificando que as regras de gate de confirmação e referência aos 5 arquivos de conhecimento estão explícitas.
- [x] 3.2 Criar `code-smells-project/.claude/skills/refactor-arch/references/01-project-analysis.md` com heurísticas agnósticas de detecção de linguagem, framework, banco de dados, domínio e arquitetura atual, e `references/03-audit-report-template.md` com o formato padronizado do relatório da Fase 2, verificando a presença de ambos os arquivos em disco.
- [x] 3.3 Criar `code-smells-project/.claude/skills/refactor-arch/references/02-anti-patterns-catalog.md` contendo no mínimo 8 anti-patterns distribuídos entre CRITICAL, HIGH, MEDIUM e LOW (incluindo obrigatoriamente detecção de APIs deprecated e todos os problemas mapeados nos 3 projetos), verificando que cada padrão possui sinais de detecção claros, severidade e recomendação.
- [x] 3.4 Criar `code-smells-project/.claude/skills/refactor-arch/references/04-mvc-architecture-guidelines.md` (regras das camadas Models, Views/Routes, Controllers, Config, Middlewares e Composition Root para Python/Flask e Node.js/Express) e `references/05-refactoring-playbook.md` (mínimo de 8 padrões de transformação com exemplos de código antes/depois cobrindo Python e Node.js), verificando que todas as 5 áreas de conhecimento obrigatórias estão atendidas.
- [x] 3.5 Replicar a skill completa de `code-smells-project/.claude/skills/refactor-arch/` para `ecommerce-api-legacy/.claude/skills/refactor-arch/`, `task-manager-api/.claude/skills/refactor-arch/` e `.agents/skills/refactor-arch/` (compatibilidade multi-agente), e documentar a seção "Construção da Skill" no `README.md`, verificando via `diff -r` que as cópias da skill nos 3 projetos são idênticas.

## 4. Auditoria e Refatoração MVC — Projeto 1 (`code-smells-project`)

- [x] 4.1 Executar a Fase 1 (Análise) e a Fase 2 (Auditoria) da skill `refactor-arch` em `code-smells-project/` e salvar o relatório gerado em `reports/audit-project-1.md`, verificando que o relatório segue o template, detecta Python/Flask e contém >= 5 findings ordenados de CRITICAL a LOW (com >= 1 CRITICAL/HIGH e linhas exatas).
- [x] 4.2 Executar a Fase 3 (Refatoração MVC) em `code-smells-project/`, reestruturando o código em `config/`, `models/`, `views/` (ou `routes/`), `controllers/`, `middlewares/` e `app.py` (composition root) sem credenciais hardcoded, SQL injection ou God Classes, e validar subindo o servidor Flask e testando todos os endpoints originais via requisições HTTP (`curl`/script).

## 5. Auditoria e Refatoração MVC — Projeto 2 (`ecommerce-api-legacy`)

- [x] 5.1 Executar a Fase 1 (Análise) e a Fase 2 (Auditoria) da skill `refactor-arch` em `ecommerce-api-legacy/` e salvar o relatório gerado em `reports/audit-project-2.md`, verificando que o relatório segue o template, detecta Node.js/Express e contém >= 5 findings ordenados de CRITICAL a LOW (com >= 1 CRITICAL/HIGH e linhas exatas).
- [x] 5.2 Executar a Fase 3 (Refatoração MVC) em `ecommerce-api-legacy/`, desmembrando `AppManager.js` na estrutura MVC (`src/config/`, `src/models/`, `src/views/` ou `src/routes/`, `src/controllers/`, `src/middlewares/` e `src/app.js`) e validar subindo o servidor Express e testando todos os endpoints de cursos, usuários e checkout definidos em `api.http`.

## 6. Auditoria e Refatoração MVC — Projeto 3 (`task-manager-api`)

- [x] 6.1 Executar a Fase 1 (Análise) e a Fase 2 (Auditoria) da skill `refactor-arch` em `task-manager-api/` e salvar o relatório gerado em `reports/audit-project-3.md`, verificando que o relatório segue o template, detecta Python/Flask (domínio Task Manager) e contém >= 5 findings ordenados de CRITICAL a LOW (com >= 1 CRITICAL/HIGH e linhas exatas).
- [x] 6.2 Executar a Fase 3 (Refatoração MVC) em `task-manager-api/`, adequando a estrutura parcialmente organizada para o padrão MVC completo (configuração externalizada, models desacoplados, controllers, views/routes e error handling centralizado) e eliminando as falhas de segurança/qualidade, validando o boot da aplicação e a resposta de todos os endpoints originais.

## 7. Validação Cruzada, Documentação Final e Entrega

- [x] 7.1 Preencher as seções "Resultados" (resumo quantitativo dos 3 relatórios, comparação antes/depois da árvore de diretórios, checklists de validação das Fases 1, 2 e 3 para os 3 projetos, logs reais de execução e observações cross-stack) e "Como Executar" no `README.md`, verificando que todas as seções exigidas pelo desafio estão completas.
- [x] 7.2 Executar verificação final de integridade do repositório (`reports/audit-project-{1,2,3}.md`, `.claude/skills/refactor-arch/` nos 3 projetos, `README.md` completo e smoke test das 3 APIs refatoradas) e realizar o commit do código refatorado e artefatos no Git, verificando com `git status` que a árvore de trabalho dos entregáveis está limpa e versionada.
