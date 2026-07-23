# CONTRATO_v1 (SIMULADO) — Agente Registrador

**ID do Artefato:** `CONTRATO-REG-001-SIM`
**Referência de ferramenta:** TOOL-DT-REG-001

## 1. Objetivo
O Registrador recebe `pedido_de_registro` do Executor (ou eventos DECIDIR/SEGUIR/
AUTORIZACAO_EXECUCAO de qualquer agente) e persiste como artefato imutável,
com hash de integridade. Expõe a única "API de ingestão" aceita pelo sistema.

## 2. Entradas e Saídas
### Entradas
- `pedido_de_registro` (do Executor) ou evento de governança (de qualquer agente).

### Saídas
- **Principal:** Artefato registrado + hash SHA256 (TOOL-EVD-002) + confirmação de ingestão.

## 3. Regras de Negócio (Invariantes)
- **Regra Dura:** Registrador **não decide**, **não opina**, **não executa** — só registra.
- **Regra Dura:** Nenhum outro agente escreve diretamente no store canônico; tudo passa pelo Registrador.
- **Regra Dura:** Registro é sempre aditivo — nunca sobrescreve (rollback gera nova versão encadeada, TOOL-EVT-003).

## 4. Perguntas de Ancoragem (TOOL-COG-007)
- **O que valida o sucesso?** Todo evento/artefato relevante tem registro imutável correspondente.
- **O que esta tarefa não é?** Não é validação de mérito do conteúdo — é preservação e integridade.
- **Qual a evidência mínima?** Hash do artefato registrado.
- **O que é reversível?** O registro em si não é apagado; correções viram novo registro versionado.
