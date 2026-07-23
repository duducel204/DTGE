# CONTRATO_v1 — Agente/Plano Rollback

**ID do Artefato:** `CONTRATO-ROLLBACK-001`
**Referência de ferramenta:** TOOL-EVT-003

## 1. Objetivo
Reverter uma execução quando a validação pós-execução falhar ou quando
autorizado explicitamente pelo humano. Rollback nunca apaga histórico —
sempre encadeia como nova versão (`prev_ref`).

## 2. Entradas e Saídas
### Entradas
- Falha detectada na execução (Executor) ou comando humano de reversão.
- Referência ao artefato/versão anterior (`prev_ref`).

### Saídas
- **Principal:** Evento `ROLLBACK` (TOOL-EVT-003) + artefato de rollback + logs/hashes pós-ação.

## 3. Regras de Negócio (Invariantes)
- **Regra Dura:** Rollback **não sobrescreve** — cria nova versão encadeada.
- **Regra Dura:** Todo plano de execução (Executor) deve ter, desde a origem, um esqueleto de rollback associado; rollback nunca é improvisado post-hoc.
- **Regra de Negócio:** Rollback executado também passa pelo Registrador (mesma regra do Executor — não escreve direto no store).

## 4. Perguntas de Ancoragem (TOOL-COG-007)
- **O que valida o sucesso?** Estado revertido para a versão anterior conhecida, com histórico preservado.
- **O que esta tarefa não é?** Não é apagar o que deu errado — é encadear a correção.
- **Qual a evidência mínima?** Arquivo de rollback + logs/hashes pós-ação.
- **O que é reversível?** O próprio rollback pode ser revertido por outro rollback, sempre encadeado.


---
**Canonizado em (UTC):** 20260716T054725Z
**Promovido de:** `CONTRATO-ROLLBACK-001-SIM` (simulação analisada e aprovada pelo humano)
