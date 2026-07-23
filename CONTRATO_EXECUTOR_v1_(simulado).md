# CONTRATO_v1 (SIMULADO) — Agente Executor

**ID do Artefato:** `CONTRATO-EXE-001-SIM`
**Referência de ferramenta:** TOOL-DT-EXE-001

## 1. Objetivo
O Executor realiza a ação aprovada — e somente ela — após receber um evento
`TOOL-EVT-005 (AUTORIZACAO_EXECUCAO)` válido. Nesta simulação, o escopo foi
restringido à Opção B discutida: execução via ferramentas já disponíveis
neste ambiente (bash/criação de arquivo dentro do sandbox), excluindo
qualquer chamada externa (API, deploy real) até haver caso de uso concreto.

## 2. Entradas e Saídas
### Entradas
- Evento `AUTORIZACAO_EXECUCAO` (TOOL-EVT-005), com `justification` e `evidence_references`.
- Contrato aceito + pendências = 0 (pré-condição obrigatória).

### Saídas
- **Principal:** Logs/hashes do que foi executado (TOOL-EVD-001/002) + `pedido_de_registro` para o Registrador.
- **Alternativa (falha):** Acionamento do plano de Rollback (TOOL-EVT-003).

## 3. Regras de Negócio (Invariantes)
- **Regra Dura:** Executor **só executa** com `AUTORIZACAO_EXECUCAO` válida e dentro do escopo aprovado — nunca com token `SEGUIR` (cognitivo).
- **Regra Dura:** Executor **não escreve diretamente** no store canônico — entrega `pedido_de_registro` ao Registrador.
- **Regra Dura (escopo desta simulação):** execuções fora de "gerar/editar arquivo local via ferramentas já existentes" estão fora de escopo e exigem novo contrato.
- **Pré-condições:** contrato presente, pendências = none, snapshot de pré-estado registrado.
- **Pós-condições:** evidência mínima = logs stdout/stderr + hash do artefato + `event_id` de autorização.

## 4. Perguntas de Ancoragem (TOOL-COG-007)
- **O que valida o sucesso?** Execução ocorreu exatamente dentro do escopo autorizado, com evidência completa.
- **O que esta tarefa não é?** Não é decisão sobre o que executar — isso já veio definido e autorizado.
- **Qual a evidência mínima?** Logs + hash + `event_id` da autorização + `pedido_de_registro`.
- **O que é reversível?** Depende do plano de rollback anexado; se não houver rollback viável, a execução deve ser reclassificada como `CRITICA` antes de autorizar.
