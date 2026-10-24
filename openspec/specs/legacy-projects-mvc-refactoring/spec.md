# legacy-projects-mvc-refactoring Specification

## Purpose

Garante a aquisição, análise manual, auditoria automatizada, refatoração para o padrão MVC e documentação completa dos 3 projetos legados do desafio (`code-smells-project`, `ecommerce-api-legacy` e `task-manager-api`).

## Requirements

### Requirement: Disponibilização e instalação da skill nos três projetos-alvo
O repositório SHALL conter os 3 projetos legados (`code-smells-project/`, `ecommerce-api-legacy/` e `task-manager-api/`), cada um possuindo uma cópia funcional da skill em `.claude/skills/refactor-arch/`.

#### Scenario: Verificação da estrutura da skill em cada projeto
- **WHEN** a estrutura de diretórios dos 3 projetos é verificada
- **THEN** `.claude/skills/refactor-arch/SKILL.md` e seus arquivos de referência em Markdown existem dentro de `code-smells-project/`, `ecommerce-api-legacy/` e `task-manager-api/`

### Requirement: Relatórios de auditoria persistidos para os três projetos
A execução da Fase 2 da skill nos 3 projetos SHALL produzir relatórios de auditoria salvos em `reports/audit-project-1.md`, `reports/audit-project-2.md` e `reports/audit-project-3.md` na raiz do repositório.

#### Scenario: Critérios mínimos de achados por relatório
- **WHEN** qualquer um dos 3 relatórios em `reports/audit-project-{1,2,3}.md` é inspecionado
- **THEN** o relatório MUST apresentar a stack correta do respectivo projeto, conter no mínimo 5 findings com arquivo e linhas exatos ordenados de `CRITICAL` a `LOW`, e incluir pelo menos 1 finding de severidade `CRITICAL` ou `HIGH`

### Requirement: Refatoração MVC com preservação funcional nos três projetos
O código-fonte de `code-smells-project`, `ecommerce-api-legacy` e `task-manager-api` SHALL ser refatorado para o padrão MVC (com camadas de Models, Views/Routes, Controllers, módulo de configuração sem credenciais hardcoded, error handling centralizado e entry point claro) mantendo 100% de compatibilidade nos endpoints HTTP originais.

#### Scenario: Validação de boot e endpoints após refatoração
- **WHEN** cada um dos 3 projetos refatorados é iniciado e seus endpoints originais são requisitados
- **THEN** a aplicação inicia sem erros de sintaxe ou importação e todos os endpoints originais retornam respostas válidas condizentes com o domínio da aplicação

### Requirement: Documentação completa do processo e análise manual no README
O arquivo `README.md` na raiz do repositório SHALL documentar todo o processo nas seções obrigatórias: "Análise Manual", "Construção da Skill", "Resultados" e "Como Executar".

#### Scenario: Validação da Análise Manual e Resultados no README
- **WHEN** o arquivo `README.md` na raiz do repositório é avaliado
- **THEN** a seção "Análise Manual" documenta no mínimo 5 problemas por projeto (sendo ao menos 1 CRITICAL/HIGH, 2 MEDIUM e 2 LOW com justificativa) e a seção "Resultados" inclui o resumo dos relatórios, comparação antes/depois, checklist de validação preenchido e logs/evidências das 3 aplicações rodando
