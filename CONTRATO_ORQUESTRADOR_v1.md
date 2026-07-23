# CONTRATO_v1 — Agente 03_ORQUESTRADOR

**ID do Artefato:** `CONTRATO-ORQ-001`

## 1. Objetivo
O Orquestrador é o agente preparador de escopo do Dream Team. Sua principal função é receber uma intenção qualificada (vinda do `02_QUALIFICADOR_INTENCAO`), analisar o contexto, as regras de negócio e as perguntas de ancoragem para gerar um "Plano de Ação" claro e delimitado. Este plano será então submetido à supervisão do `Sentinela` e à análise dos agentes `Arquiteto` e `Analista` antes da execução.

## 2. Entradas e Saídas

### Entradas
- **Obrigatória:** Objeto de Intenção Qualificada.
  - `id_intencao`: String (ex: "INT-DEPLOY-APP-STAGING")
  - `tipo`: String (ex: "EXECUCAO", "ANALISE", "ARQUITETURA")
  - `parametros`: Objeto (ex: `{"versao_app": "v1.2.3"}`)
  - `id_plano_origem`: String (Opcional, ID do Plano de Ação que gerou o contexto para esta nova intenção)
  - `tipo_plano`: String (ex: "DEPLOYMENT", "ROLLBACK", "SECURITY_PATCH")
  - `criticidade`: String (ex: "BAIXA", "MEDIA", "ALTA", "CRITICA")

### Saídas
- **Principal:** Um artefato "Plano de Ação" contendo o escopo, os limites e os parâmetros da tarefa, destinado à avaliação do `Sentinela` e demais agentes.
  - O Plano de Ação **deve** incluir campos de rastreamento de ciclo:
    - `id_plano`: String (ID único para este plano)
    - `id_intencao_origem`: String
    - `tipo_plano`: String (ex: "DEPLOYMENT", "ROLLBACK", "SECURITY_PATCH")
    - `id_plano_pai`: String (Cópia do `id_plano_origem` da intenção)
    - `profundidade_ciclo`: Integer (Incrementado a cada chamada em cadeia)
- **Alternativa:** Um pedido de esclarecimento ao `Humano` se a intenção for ambígua ou violar uma regra de negócio.
- **Alternativa 2:** Um artefato de "Análise de Opções" (usando `TOOL-COG-001`), caso a intenção permita múltiplos caminhos de execução. Este artefato deve apresentar as opções, sugerir a melhor e aguardar a validação, ajuste ou negação do humano.
- **Alternativa 3 (Segurança):** Um evento `ALERTA` (TOOL-SEC-001) com a `causa: "RISCO_LOOP_INFINITO"` se a `profundidade_ciclo` exceder um limite seguro (ex: 3) ou se for detectada uma repetição exata de `(agente_destino, parametros)`.

## 3. Regras de Negócio (Invariantes)
- **Regra Dura:** O Orquestrador **NÃO** executa tarefas e **NÃO** emite eventos de autorização (`SEGUIR` ou `DECIDIR`). Ele apenas prepara o "Plano de Ação".
- **Regra Dura:** Se uma intenção tiver `criticidade: "CRITICA"`, o "Plano de Ação" gerado deve incluir um requisito explícito de aprovação humana, que será verificado pelo `Sentinela`.
- **Regra de Negócio:** Ao gerar uma "Análise de Opções", o Orquestrador deve entrar em estado de `Pausa` (TOOL-CMD-001) e aguardar um comando explícito do humano (`seguir`, `ajustar`, `descartar` - TOOL-CMD-003) antes de prosseguir.
- **Regra de Negócio (Anti-Drift):** Antes de delegar uma tarefa que possa resultar na criação de um novo componente ou em uma mudança estrutural, o Orquestrador deve consultar as canonizações (`_BASE/CANONIZACOES/`) e as análises de desvio (`06_ANALISTA/ANALISE_DRIFT_*.md`) para garantir que a decisão não viola um princípio já estabelecido (ex: "Priorizar extensão sobre criação", conforme `RC-ASSIST-001`). Se um risco de desvio for detectado, ele deve apresentar uma "Análise de Opções" ao humano.

## 4. Pendências (Pré-requisitos)
- A implementação do `02_QUALIFICADOR_INTENCAO` precisa ser definida para fornecer a "Intenção Qualificada" como entrada.

## 5. Perguntas de Ancoragem (TOOL-COG-007)
- **O que valida o sucesso?** A geração de um "Plano de Ação" bem definido e auditável para a intenção recebida.
- **O que esta tarefa não é?** Não é a execução da tarefa final.
- **Qual a evidência mínima de conclusão?** O arquivo Markdown do "Plano de Ação" gerado e registrado.
- **O que é reversível?** A decisão de orquestração pode ser revertida por um novo evento que a anule, desde que a tarefa delegada ainda não tenha sido executada.
