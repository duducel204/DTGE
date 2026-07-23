# CONTRATO_v1 — Agente 04_EXECUTOR

**ID do Artefato:** `CONTRATO-EXE-001`
**Promovido de:** `CONTRATO-EXE-001-SIM` (simulação, Opção B validada pelo Analista)
**Data de Geração (UTC):** 2026-07-16

## 1. Objetivo
O Executor realiza a ação aprovada — e somente ela — após receber um evento
`TOOL-EVT-005 (AUTORIZACAO_EXECUCAO)` válido e dentro do escopo aprovado.

**Escopo desta versão (restrito, Opção B):** execução via ferramentas já
disponíveis neste ambiente — comandos bash e criação/edição de arquivo,
dentro do sandbox local. Qualquer execução fora disso (chamada de API
externa, deploy real, rede) está **fora de escopo** e exige novo contrato.

## 2. Entradas e Saídas

### Entradas
- **Obrigatória:** Token de autorização (`TOOL-EVT-005`), contendo no mínimo:
  `event_type`, `event_name`, `decision`, `justification`, `request_id`.
- **Obrigatória:** Referência ao contrato aceito (este arquivo) + lista de pendências (deve estar vazia).
- **Opcional:** `prev_ref` quando a ação fizer parte de uma cadeia de rollback.

### Saídas
- **Principal:** Resultado da execução (stdout/stderr/returncode ou caminho do arquivo criado) + evidência (log + hash) + `pedido_de_registro`.
- **Alternativa (falha na execução):** Registro de falha + acionamento do plano de Rollback (`TOOL-EVT-003`).
- **Alternativa (token inválido):** Recusa explícita, sem qualquer execução, com motivo registrado.

## 3. Regras de Negócio (Invariantes)
- **Regra Dura:** Executor **só executa** com um token cujo `event_type == "TOOL-EVT-005"` e `decision == "EXECUTION_AUTHORIZED"`.
- **Regra Dura:** Token com `event_name == "SEGUIR"` (ou qualquer tipo que não seja `AUTORIZACAO_EXECUCAO`) é **recusado explicitamente** — nunca interpretado como autorização implícita.
- **Regra Dura:** Pré-condições obrigatórias antes de qualquer execução:
  1. Este contrato deve existir e estar acessível.
  2. Lista de pendências fornecida deve estar vazia.
  3. Um snapshot de pré-estado deve ser registrado antes da ação.
- **Regra Dura:** Executor **não escreve diretamente** em nenhum "store canônico" — ele gera um `pedido_de_registro` (artefato) destinado ao Registrador.
  - **Pendência declarada:** o Registrador ainda não foi formalizado nesta conversa (existe só como contrato simulado). Até lá, o `pedido_de_registro` fica como artefato de arquivo aguardando ingestão futura — isso é uma limitação conhecida, não uma violação da regra.
- **Regra Dura:** Toda execução gera evidência mínima: log (stdout/stderr quando aplicável) + hash SHA256 do artefato afetado + `event_id` do token que autorizou.
- **Regra de Negócio:** Se a execução falhar, o Executor não tenta corrigir sozinho — apenas registra a falha e sinaliza necessidade de Rollback.

## 4. Pendências (Pré-requisitos)
- Registrador real ainda não existe nesta conversa — `pedido_de_registro` fica como artefato pendente de ingestão manual até lá.
- Plano de Rollback real (código) ainda não existe — hoje o Executor apenas sinaliza a necessidade; não executa reversão automática.

## 5. Perguntas de Ancoragem (TOOL-COG-007)
- **O que valida o sucesso?** Execução ocorreu exatamente dentro do escopo autorizado, com evidência completa e verificável.
- **O que esta tarefa não é?** Não é decisão sobre o que executar — isso já veio definido e autorizado por evento externo ao Executor.
- **Qual a evidência mínima de conclusão?** Log de execução + hash do artefato + `event_id` da autorização + `pedido_de_registro` gerado.
- **O que é reversível?** Depende do plano de rollback anexado à ação; ações sem rollback viável não deveriam ser autorizadas como `AUTORIZACAO_EXECUCAO` direta sem essa ressalva.
