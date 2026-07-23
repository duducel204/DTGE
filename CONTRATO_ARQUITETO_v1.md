# CONTRATO_v1 — Agente Arquiteto

**ID do Artefato:** `CONTRATO-ARQ-001`
**Referência de ferramenta:** TOOL-DT-ARQ-001

## 1. Objetivo
O Arquiteto recebe o Plano de Ação (já auditado pelo Sentinela) e modela a
solução em estados explícitos, dependências, pontos de controle e critérios
de rollback — sem escrever código de execução final.

## 2. Entradas e Saídas
### Entradas
- Plano de Ação + Registro de Riscos do Sentinela.

### Saídas
- **Principal:** Artefato de arquitetura — estados, fluxo sequencial, dependências, pontos de controle, esqueleto de rollback (TOOL-EVT-003).
- **Alternativa:** Pedido de esclarecimento ao Orquestrador se dependências forem ambíguas.

## 3. Regras de Negócio (Invariantes)
- **Regra Dura:** Arquiteto **não executa** e **não decide** — projeta.
- **Regra Dura:** Todo desenho de solução deve incluir plano de rollback mínimo, mesmo que esqueleto.
- **Regra de Negócio (Anti-Drift):** Antes de propor novo componente, consultar canonizações existentes; priorizar extensão sobre criação (RC-ASSIST-001).

## 4. Perguntas de Ancoragem (TOOL-COG-007)
- **O que valida o sucesso?** Arquitetura completa, com pontos de controle e rollback definidos.
- **O que esta tarefa não é?** Não é a implementação em código.
- **Qual a evidência mínima?** Artefato de arquitetura (MD) + mapa de interfaces.
- **O que é reversível?** Sim — arquitetura pode ser revisada antes da fase de execução.


---
**Canonizado em (UTC):** 20260716T054725Z
**Promovido de:** `CONTRATO-ARQ-001-SIM` (simulação analisada e aprovada pelo humano)
