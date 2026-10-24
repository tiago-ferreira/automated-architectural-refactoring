# refactor-arch-skill Specification

## Purpose

Fornece uma skill agêntica reutilizável e agnóstica de tecnologia (`refactor-arch`) que analisa codebases legadas, audita anti-patterns arquiteturais/de segurança e executa a refatoração automatizada para o padrão MVC com validação funcional.

## Requirements

### Requirement: Execução estruturada em três fases sequenciais
A skill `refactor-arch` SHALL operar estritamente em 3 fases sequenciais: Fase 1 (Análise de Projeto), Fase 2 (Auditoria Arquitetural com confirmação humana obrigatória) e Fase 3 (Refatoração para MVC e Validação).

#### Scenario: Pausa obrigatória entre Fase 2 e Fase 3
- **WHEN** a skill conclui a Fase 2 e apresenta o relatório de auditoria ao usuário
- **THEN** a skill MUST aguardar confirmação explícita do usuário antes de criar, modificar ou remover qualquer arquivo de código do projeto-alvo

### Requirement: Detecção agnóstica de tecnologia na Fase 1
Na Fase 1, a skill SHALL inspecionar o diretório do projeto-alvo e identificar linguagem, framework, dependências principais, domínio da aplicação, arquitetura atual, quantidade de arquivos-fonte analisados e tabelas/entidades de dados sem depender de uma stack fixa.

#### Scenario: Análise de projeto Python/Flask ou Node.js/Express
- **WHEN** a Fase 1 é executada em um projeto Python/Flask ou Node.js/Express
- **THEN** a skill imprime o bloco `PHASE 1: PROJECT ANALYSIS` com a linguagem, framework, domínio, arquitetura atual e total de arquivos-fonte correspondentes à realidade do projeto

### Requirement: Base de conhecimento com cinco áreas obrigatórias em Markdown
A skill SHALL ser acompanhada por arquivos de referência em formato Markdown que cubram obrigatoriamente: (1) heurísticas de análise de projeto, (2) catálogo de anti-patterns, (3) template de relatório de auditoria, (4) guidelines de arquitetura MVC e (5) playbook de refatoração.

#### Scenario: Verificação de completude do catálogo e playbook
- **WHEN** os arquivos de referência da skill são inspecionados
- **THEN** o catálogo MUST conter no mínimo 8 anti-patterns distribuídos entre CRITICAL, HIGH, MEDIUM e LOW (incluindo detecção de APIs deprecated) e o playbook MUST conter no mínimo 8 padrões de transformação com exemplos de código antes/depois

### Requirement: Relatório de auditoria padronizado na Fase 2
Na Fase 2, a skill SHALL cruzar o código-fonte analisado com o catálogo de anti-patterns e gerar um relatório seguindo o template de referência, ordenado da severidade `CRITICAL` até `LOW`, indicando arquivo e linhas exatas (`arquivo:linha_inicial-linha_final`), descrição, impacto e recomendação.

#### Scenario: Geração de relatório com achados rastreáveis
- **WHEN** a Fase 2 audita um projeto legado com problemas de arquitetura, segurança e qualidade
- **THEN** o relatório lista pelo menos 5 achados (incluindo ao menos 1 `CRITICAL` ou `HIGH`) com localização exata de arquivo e linha e sumário quantitativo por severidade

### Requirement: Refatoração adaptativa para MVC e validação na Fase 3
Na Fase 3, após confirmação do usuário, a skill SHALL reestruturar o projeto para o padrão MVC separando responsabilidades em Models, Views/Routes, Controllers, configuração externalizada e tratamento centralizado de erros, validando ao final que a aplicação inicia sem erros e todos os endpoints continuam respondendo.

#### Scenario: Adaptação a diferentes níveis de organização prévia
- **WHEN** a Fase 3 é executada tanto em um projeto monolítico quanto em um projeto parcialmente organizado em camadas
- **THEN** a skill adapta a transformação para atingir o padrão MVC limpo sem quebrar o boot da aplicação nem o contrato dos endpoints existentes
