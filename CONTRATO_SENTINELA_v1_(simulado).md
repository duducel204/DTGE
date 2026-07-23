# CONTRATO_v1 (SIMULADO) — Agente Sentinela

**ID do Artefato:** `CONTRATO-SEN-001-SIM`
**Referência de ferramenta:** TOOL-DT-SEN-001

## 1. Objetivo
O Sentinela recebe o Plano de Ação do Orquestrador e audita riscos técnicos,
estratégicos e cognitivos antes que o plano siga para Arquiteto/Analista.
Não propõe solução, não decide — só sinaliza.

## 2. Entradas e Saídas
### Entradas
- Plano de Ação (do Orquestrador), incluindo `criticidade` e `profundidade_ciclo`.

### Saídas
- **Principal:** Registro de riscos (TOOL-DT-SEN-001) — lista de riscos + mitigação sugerida.
- **Alternativa:** Evento `ALERTA_INTEGRIDADE` (TOOL-EVT-004) se detectar violação de integridade/segurança.
- **Bloqueio:** Se `criticidade: CRITICA` sem requisito de aprovação humana explícito no plano, o Sentinela bloqueia o avanço e devolve ao Orquestrador.

## 3. Regras de Negócio (Invariantes)
- **Regra Dura:** Sentinela **não decide** e **não executa** — apenas identifica e registra.
- **Regra Dura:** Todo plano com `profundidade_ciclo > 3` ou repetição exata de `(agente_destino, parametros)` é barrado aqui, mesmo que o Orquestrador não tenha emitido o alerta.
- **Regra de Negócio:** Vieses cognitivos (TOOL-COG-002) são checados explicitamente: fechamento precoce, confirmação, autoridade implícita.

## 4. Perguntas de Ancoragem (TOOL-COG-007)
- **O que valida o sucesso?** Todos os riscos relevantes identificados antes da fase de arquitetura.
- **O que esta tarefa não é?** Não é aprovação nem reprovação do plano — é sinalização.
- **Qual a evidência mínima?** Registro de riscos + mitigação proposta.
- **O que é reversível?** Sim — o registro de riscos pode ser reaberto se novo dado surgir.
