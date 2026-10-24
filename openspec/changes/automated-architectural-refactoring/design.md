# Design

## Context

O workspace atual contém apenas o documento de especificação do desafio (`refatoracao-arquitetural-organizado.md`) e a configuração do OpenSpec. Os 3 projetos legados (`code-smells-project`, `ecommerce-api-legacy`, `task-manager-api`) residem no repositório base oficial `https://github.com/devfullcycle/mba-ia-refactor-projects-skill`.

O desafio exige três frentes técnicas coordenadas (veja `proposal.md` para motivação e `specs/` para contratos de comportamento):
1. Obtenção e inspeção manual dos 3 projetos legados (duas aplicações Python/Flask com níveis distintos de organização e uma aplicação Node.js/Express).
2. Engenharia de uma Skill agêntica (`refactor-arch`) com arquivos de referência modulares em Markdown capaz de operar em 3 fases (Análise, Auditoria com gate humano e Refatoração MVC + Validação) sem acoplamento de linguagem.
3. Execução da auditoria e refatoração nos 3 projetos, salvando relatórios em `reports/audit-project-{1,2,3}.md` e documentando todo o trabalho em `README.md`.

## Goals / Non-Goals

**Goals:**
- Projetar a anatomia da skill `refactor-arch` com separação clara entre orquestração de fluxo (`SKILL.md`) e conhecimento de domínio (`references/*.md`), evitando sobrecarga de contexto (progressive disclosure).
- Definir uma arquitetura MVC alvo flexível que se adapte tanto a projetos Python/Flask quanto Node.js/Express, e tanto a monolitos em poucos arquivos quanto a projetos parcialmente divididos em camadas.
- Garantir compatibilidade multi-agente instalando a skill em `.claude/skills/refactor-arch/` dentro de cada um dos 3 projetos (requisito obrigatório do entregável) e disponibilizando-a também em `.agents/skills/refactor-arch/` quando aplicável ao ambiente local.
- Assegurar que a Fase 3 da refatoração preserve 100% dos contratos HTTP (rotas, métodos, status codes e payloads JSON) de cada aplicação.

**Non-Goals:**
- Alterar o banco de dados subjacente (ex.: trocar SQLite/memória por PostgreSQL) ou introduzir ORMs pesados não previstos nas dependências originais dos projetos.
- Adicionar autenticação/autorização nova em rotas que originalmente eram públicas, o que quebraria testes automatizados e contratos esperados pelos endpoints originais.
- Criar interfaces gráficas (frontend HTML/CSS) — em APIs REST, a camada "View" do MVC corresponde à camada de apresentação HTTP (Routes/Serializers/Presenters).

## Decisions

### 1. Anatomia da Skill e Organização dos Arquivos de Referência
- **Decisão**: Estruturar `.claude/skills/refactor-arch/` com um `SKILL.md` enxuto focado no controle de estado das 3 fases e 5 arquivos de referência dedicados em `references/`:
  1. `references/01-project-analysis.md` (Heurísticas de detecção de linguagem, framework, banco, domínio e topologia arquitetural).
  2. `references/02-anti-patterns-catalog.md` (Catálogo de >= 10 anti-patterns distribuídos entre CRITICAL, HIGH, MEDIUM e LOW, incluindo SQL Injection, Hardcoded Credentials, God Class/Method, Fat Controllers, Tight Coupling/No DI, Mutable Global State, N+1 Queries, Deprecated APIs, Missing Input Validation e Magic Numbers/Poor Naming).
  3. `references/03-audit-report-template.md` (Template estrito do relatório da Fase 2 com cabeçalho, sumário por severidade e blocos padronizados por finding).
  4. `references/04-mvc-architecture-guidelines.md` (Diretrizes de MVC para APIs REST em Python/Flask e Node.js/Express: Models, Views/Routes, Controllers, Config, Middlewares/Error Handling e Composition Root).
  5. `references/05-refactoring-playbook.md` (Playbook com >= 10 transformações práticas antes/depois em Python/Flask e Node.js/Express mapeadas 1-para-1 com o catálogo de anti-patterns).
- **Alternativas consideradas**: Colocar todo o conhecimento dentro de um único `SKILL.md` monolítico ou dividir em dezenas de micro-arquivos.
- **Racional**: Um `SKILL.md` único de milhares de linhas dilui a atenção do LLM nas regras críticas (como o gate de confirmação da Fase 2 e o formato exato de saída). Cinco arquivos numerados espelham exatamente as 5 áreas obrigatórias do desafio e permitem leitura direcionada por fase (Fase 1 lê `01`, Fase 2 lê `02` e `03`, Fase 3 lê `04` e `05`).

### 2. Mapeamento do Padrão MVC para APIs REST (Python/Flask e Node.js/Express)
- **Decisão**: Padronizar a responsabilidade das camadas MVC respeitando as convenções idiomáticas de cada stack e mantendo um entry point compatível:
  - **Config (`config/`)**: Extração de variáveis sensíveis (`SECRET_KEY`, credenciais, portas, paths de banco) lendo de variáveis de ambiente (`os.environ` / `process.env`) com fallbacks seguros apenas para desenvolvimento.
  - **Models (`models/`)**: Encapsulamento do acesso a dados (queries SQL parametrizadas ou estruturas em memória) e regras de integridade da entidade. Proibido acessar objetos `request`/`res` HTTP.
  - **Controllers (`controllers/`)**: Orquestração do fluxo de negócio, validação de regras de domínio e coordenação entre um ou mais Models.
  - **Views / Routes (`views/` ou `routes/`)**: Definição de rotas HTTP (Flask Blueprints ou Express Routers), extração/validação básica de parâmetros de entrada e formatação da resposta HTTP/JSON (camada de apresentação da API).
  - **Middlewares (`middlewares/`)**: Tratamento centralizado de exceções/erros HTTP e middlewares transversais.
  - **Composition Root (`app.py` / `src/app.js`)**: Inicialização limpa do servidor, registro de blueprints/routers e injeção de dependências.
- **Alternativas consideradas**: Forçar exatamente a mesma árvore de pastas (ex.: obrigar `src/` em projetos Flask que rodam `python app.py` na raiz).
- **Racional**: Em projetos Flask existentes (`code-smells-project` e `task-manager-api`), manter `app.py` na raiz do projeto (importando de `config/`, `models/`, `views/`, `controllers/`, `middlewares/` ou de pacotes equivalentes) evita quebrar comandos de inicialização (`python app.py` ou `flask run`), enquanto em Node.js (`ecommerce-api-legacy`) preserva-se `src/app.js` conforme `package.json`.

### 3. Estratégia de Aquisição do Repositório Base e Controle de Versão
- **Decisão**: Na etapa inicial de implementação, clonar `https://github.com/devfullcycle/mba-ia-refactor-projects-skill` em um diretório temporário, copiar os 3 projetos (`code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/`) para a raiz do workspace (e inicializar o repositório git caso necessário), preservando uma cópia ou snapshot do estado original antes da Fase 3 para permitir comparação exata antes/depois e reexecução limpa se necessário.
- **Alternativas consideradas**: Submódulos Git separados para cada projeto.
- **Racional**: O entregável exige um único repositório contendo as pastas dos 3 projetos refatorados, `reports/` e `README.md` commitados diretamente na árvore principal.

### 4. Estratégia de Validação Funcional na Fase 3
- **Decisão**: Automatizar o teste de fumaça (smoke test) ao final da Fase 3 de cada projeto subindo a aplicação em background (em porta dedicada/livre), executando requisições HTTP contra todos os endpoints mapeados na Fase 1 (via `curl` ou script de teste) e verificando status codes `2xx`/`4xx` esperados antes de encerrar o processo.
- **Alternativas consideradas**: Validar apenas compilação estática (`py_compile` / `node --check`).
- **Racional**: Checagem sintática não detecta erros em tempo de execução como imports circulares em rotas, queries SQL malformadas após extração para Models ou bindings quebrados de métodos em classes JavaScript (`this` perdido em Express handlers).

## Risks / Trade-offs

- **[Risco] Regressão em contratos de API durante a extração de God Classes/Controllers** → **Mitigação**: Mapear na Fase 1 a lista completa de rotas, métodos HTTP, formatos de payload e status codes de cada projeto antes de alterar qualquer arquivo, e validar cada rota no smoke test da Fase 3.
- **[Risco] Perda de contexto de `this` em Controllers Node.js/Express ao desmembrar `AppManager.js`** → **Mitigação**: Incluir regra explícita em `04-mvc-architecture-guidelines.md` e `05-refactoring-playbook.md` para usar arrow functions nos roteadores (`router.post('/checkout', (req, res, next) => controller.checkout(req, res, next))`) ou `.bind(controller)`.
- **[Risco] Projeto 3 (`task-manager-api`) já possuir pastas `models/`, `routes/`, `services/` e a refatoração causar duplicação de camadas** → **Mitigação**: Projetar heurística adaptativa na Fase 3 para inspecionar a estrutura prévia, consolidando ou reorganizando `services/`/`routes/` dentro do padrão MVC (`models/`, `views/` ou `routes/`, `controllers/`, `config/`, `middlewares/`) sem deixar arquivos órfãos.
- **[Risco] Divergência entre achados da Análise Manual e achados da Fase 2 da Skill** → **Mitigação**: Realizar a análise manual primeiro, garantindo que todos os anti-patterns reais presentes nos 3 projetos estejam representados com sinais claros de detecção em `02-anti-patterns-catalog.md`.

## Migration Plan

1. **Preparação do Repositório**: Inicializar Git (se aplicável) e importar os 3 projetos originais de `https://github.com/devfullcycle/mba-ia-refactor-projects-skill`.
2. **Baseline e Análise Manual**: Inspecionar o código original dos 3 projetos, testar seus endpoints originais para registrar o comportamento baseline e documentar os problemas na seção de Análise Manual.
3. **Construção da Skill `refactor-arch`**: Criar `.claude/skills/refactor-arch/SKILL.md` e os 5 arquivos em `references/` no projeto 1, replicando para os projetos 2 e 3 (e `.agents/skills/refactor-arch/`).
4. **Execução Projeto a Projeto (Projetos 1, 2 e 3)**:
   - Executar Fase 1 (Análise) e Fase 2 (Auditoria).
   - Salvar o relatório gerado em `reports/audit-project-{1,2,3}.md`.
   - Executar Fase 3 (Refatoração MVC) e rodar bateria de validação de boot + endpoints.
5. **Documentação e Consolidação**: Preencher `README.md` com Análise Manual, Construção da Skill, Resultados (checklists, comparativos e logs reais) e Como Executar, seguido de commit final.
