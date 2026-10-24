# 03 — Template do Relatório de Auditoria Arquitetural (Fase 2)

Este arquivo define o formato **obrigatório e estrito** para o relatório de auditoria gerado na **Fase 2** da skill `refactor-arch` e salvo em `reports/audit-project-{N}.md`.

---

## Regras de Formatação do Relatório

1. **Ordem de Severidade**: Todos os findings devem ser listados em ordem decrescente de criticidade:
   `CRITICAL` → `HIGH` → `MEDIUM` → `LOW`.
2. **Quantidade Mínima**: O relatório deve conter **no mínimo 5 findings** (sendo obrigatório ao menos 1 `CRITICAL` ou `HIGH`). Recomenda-se listar todos os achados relevantes (tipicamente de 8 a 14 findings por projeto legado).
3. **Localização Exata**: O campo `File:` deve indicar o arquivo relativo à raiz do projeto e o intervalo de linhas exato (`arquivo.ext:linha_inicial-linha_final` ou múltiplas ocorrências separadas por vírgula).
4. **Detecção de APIs Deprecated**: Quando o projeto utilizar chamadas obsoletas (ex.: `Model.query.get()` do SQLAlchemy 1.x ou `datetime.utcnow()` do Python), inclua um finding dedicado descrevendo a API depreciada e o substituto moderno.
5. **Confirmação Obrigatória**: Ao exibir o relatório no terminal durante a execução interativa da Fase 2, finalize sempre com a pergunta:
   `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`

---

## Estrutura Exata do Template

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-diretorio-do-projeto>
Stack:   <Linguagem> + <Framework e versão>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <C> | HIGH: <H> | MEDIUM: <M> | LOW: <L>

## Findings

### [CRITICAL] <Nome do Anti-Pattern / Problema>
File: <caminho/arquivo.ext>:<linha_inicio>-<linha_fim>
Description: <Explicação técnica objetiva do problema encontrado no código, citando trechos/variáveis reais.>
Impact: <Impacto direto em segurança, arquitetura, testabilidade ou estabilidade da aplicação.>
Recommendation: <Ação concreta para corrigir o problema na Fase 3 (padrão MVC / segurança).>

### [HIGH] <Nome do Anti-Pattern / Problema>
File: <caminho/arquivo.ext>:<linha_inicio>-<linha_fim>
Description: <Explicação técnica objetiva do problema encontrado no código.>
Impact: <Impacto direto na manutenção, acoplamento, integridade de dados ou princípios SOLID.>
Recommendation: <Ação concreta para corrigir o problema na Fase 3.>

### [MEDIUM] <Nome do Anti-Pattern / Problema>
File: <caminho/arquivo.ext>:<linha_inicio>-<linha_fim>
Description: <Explicação técnica objetiva do problema (ex.: N+1 queries, APIs deprecated, falta de error handler).>
Impact: <Impacto em performance, compatibilidade futura ou confiabilidade.>
Recommendation: <Ação concreta para corrigir o problema na Fase 3.>

### [LOW] <Nome do Anti-Pattern / Problema>
File: <caminho/arquivo.ext>:<linha_inicio>-<linha_fim>
Description: <Explicação técnica objetiva (ex.: magic numbers, variáveis crípticas, código morto, prints).>
Impact: <Impacto na legibilidade, padronização e manutenibilidade do código.>
Recommendation: <Ação concreta para corrigir o problema na Fase 3.>

================================
Total: <TOTAL> findings
================================
```
