# DTGE
Sistema de governança do dream team
# DTGE (Dream Team Governance Engine)

Framework de governança multiagente para auditoria, rastreabilidade, controle de integridade e automação segura.

---

## 1. Arquitetura e Stack
* **Ambiente Principal:** Python, Termux (Android Mobile), PowerShell / CLI[span_0](start_span)[span_0](end_span).
* **Princípios:** Automação máxima, scripts idempotentes, execução atômica, estados explícitos e logs como prova[span_1](start_span)[span_1](end_span).
* **Segurança:** Proibição de execução implícita; separação estrita entre fases de pensamento (`SEGUIR`), planejamento (`DECIDIR`) e alteração real (`AUTORIZACAO_EXECUCAO`)[span_2](start_span)[span_2](end_span).

---

## 2. Inventário de Agentes e Módulos
O pipeline é composto por componentes modulares independentes integrados via camada de logs imutáveis:

| Módulo / Agente | Função Principal | Status |
| :--- | :--- | :--- |
| `01_Coletor_Continuidade` | Recupera histórico de estados, variáveis de sessão e profundidade de ciclos. | Base / Integrado |
| `02_QUALIFICADOR_INTENCAO` | Valida criticidade, aplica deduplicação de 60s e previne loops infinitos. | Funcional |
| `orquestrador.py` | Gerencia o fluxo de execução macro e transições de estado[span_3](start_span)[span_3](end_span). | Ativo |
| `sentinela.py` | Monitora integridade, desvios estruturais e alertas de risco[span_4](start_span)[span_4](end_span). | Ativo |
| `arquiteto.py` | Desenha opções, trade-offs e estruturas técnicas[span_5](start_span)[span_5](end_span). | Ativo |
| `analista.py` | Processa dados factuais e métricas de desempenho[span_6](start_span)[span_6](end_span). | Ativo |
| `executor.py` | Executa rotinas atômicas estritamente mediante autorização formal[span_7](start_span)[span_7](end_span). | Ativo |
| `dtge_logger.py` | Motor centralizado de auditoria com persistência de hashes SHA-256 e JSONL[span_8](start_span)[span_8](end_span). | Ativo |

---

## 3. Estrutura de Diretórios
```text
dtge/
├── artefatos/
│   ├── intencoes_qualificadas/  # Saídas estruturadas do Agente 02
│   ├── cache_dedup_intencoes.jsonl # Controle temporário de deduplicação
│   └── logs_auditoria.jsonl     # Trilha imutável de eventos
├── src/
│   └── dtge/                    # Módulos principais dos agentes
├── ferramenta_qualificador_intencao_standalone.py
├── dtge_logger.py
└── README.md
