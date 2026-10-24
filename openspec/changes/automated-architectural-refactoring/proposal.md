# Proposal

## Why

Revisar, auditar e refatorar manualmente múltiplos sistemas legados com problemas graves de arquitetura, segurança e qualidade de código demanda dias de esforço repetitivo e está sujeito a falhas humanas. A construção de uma Skill agêntica agnóstica de tecnologia (`refactor-arch`) automatiza a análise arquitetural, a detecção de anti-patterns/code smells com severidades padronizadas (CRITICAL a LOW) e a migração segura para o padrão MVC (Model-View-Controller), validando sua eficácia prática em 3 projetos legados distintos (Python/Flask e Node.js/Express).

## What Changes

- **Aquisição e preparação dos projetos-alvo**: Integração dos 3 projetos legados do repositório base (`code-smells-project`, `ecommerce-api-legacy`, `task-manager-api`) no workspace.
- **Análise manual de baseline**: Inspeção e documentação de no mínimo 5 problemas por projeto (distribuídos entre CRITICAL/HIGH, MEDIUM e LOW) para guiar o design da skill e compor a seção de Análise Manual do `README.md`.
- **Criação da Skill `refactor-arch`**:
  - Definição do prompt orquestrador `SKILL.md` estruturado em 3 fases sequenciais: Fase 1 (Análise da stack e arquitetura), Fase 2 (Auditoria de anti-patterns com pausa obrigatória para confirmação humana) e Fase 3 (Refatoração para MVC e validação de boot/endpoints).
  - Criação dos arquivos de referência em Markdown cobrindo as 5 áreas de conhecimento obrigatórias: (1) Heurísticas de Análise de Projeto, (2) Catálogo de Anti-Patterns (mínimo de 8 padrões incluindo detecção de APIs deprecated), (3) Template de Relatório de Auditoria, (4) Guidelines de Arquitetura MVC e (5) Playbook de Refatoração com exemplos antes/depois (mínimo de 8 transformações).
  - Instalação da skill em `.claude/skills/refactor-arch/` dentro de cada um dos 3 projetos (e espelhamento opcional em `.agents/skills/refactor-arch/` para suporte multi-agente no Antigravity/Claude Code).
- **Execução da Auditoria e Refatoração MVC nos 3 projetos**:
  - Geração e persistência dos relatórios de auditoria padronizados em `reports/audit-project-1.md`, `reports/audit-project-2.md` e `reports/audit-project-3.md`.
  - Refatoração completa do `code-smells-project` (Python/Flask monolítico) para arquitetura MVC com configurações externalizadas e tratamento de erros centralizado.
  - Refatoração completa do `ecommerce-api-legacy` (Node.js/Express com God Class `AppManager`) para arquitetura MVC mantendo o fluxo de checkout e contratos HTTP.
  - Refatoração e adequação arquitetural/segurança do `task-manager-api` (Python/Flask parcialmente estruturado) para MVC limpo sem regressão funcional.
- **Documentação final (`README.md`)**: Consolidação das seções "Análise Manual", "Construção da Skill", "Resultados" (com checklists, comparativos antes/depois e logs de validação) e "Como Executar".

## Capabilities

### New Capabilities
- `refactor-arch-skill`: Define o comportamento, estrutura de 3 fases (Análise, Auditoria com gate de confirmação, Refatoração MVC + Validação) e os 5 módulos de referência obrigatórios da skill agnóstica `refactor-arch`.
- `legacy-projects-mvc-refactoring`: Define os requisitos de auditoria (`reports/audit-project-{1,2,3}.md`), refatoração arquitetural para MVC, preservação de contratos de API/endpoints e documentação (`README.md`) aplicados aos 3 projetos-alvo (`code-smells-project`, `ecommerce-api-legacy`, `task-manager-api`).

### Modified Capabilities
<!-- Nenhuma capability existente está sendo modificada. -->

## Impact

- **Projetos e Código-Fonte**: Criação e refatoração estrutural completa nos diretórios `code-smells-project/`, `ecommerce-api-legacy/` e `task-manager-api/`.
- **Skills Agênticas**: Adição de `.claude/skills/refactor-arch/` em cada um dos 3 projetos (e `.agents/skills/refactor-arch/` na raiz para compatibilidade multi-agente).
- **Artefatos de Auditoria e Documentação**: Geração de `reports/audit-project-1.md`, `reports/audit-project-2.md`, `reports/audit-project-3.md` e `README.md` na raiz do repositório.
- **APIs e Contratos Externos**: Nenhuma quebra de contrato HTTP externo nos 3 projetos — todos os endpoints originais devem continuar respondendo com o mesmo comportamento funcional após a migração interna para MVC.
