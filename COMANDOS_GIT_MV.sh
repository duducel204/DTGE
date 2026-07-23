#!/bin/bash
set -e
mkdir -p src/dtge contracts canonizations var
git mv dreamteam_core.py src/dtge/core.py
git mv ferramenta_orquestrador_standalone.py src/dtge/orquestrador.py
git mv ferramenta_executor_standalone.py src/dtge/executor.py
git mv ferramenta_sentinela_standalone.py src/dtge/sentinela.py
git mv ferramenta_arquiteto_standalone.py src/dtge/arquiteto.py
git mv ferramenta_analista_standalone.py src/dtge/analista.py
git mv ferramenta_registrador_standalone.py src/dtge/registrador.py
git mv ferramenta_rollback_standalone.py src/dtge/rollback.py
git mv token_autorizacao_dtge.py src/dtge/token_autorizacao.py
git mv CONTRATO_ORQUESTRADOR_v1.md contracts/CONTRATO_ORQUESTRADOR_v1.md
git mv CONTRATO_EXECUTOR_v1.md contracts/CONTRATO_EXECUTOR_v1.md
git mv CONTRATO_SENTINELA_v1.md contracts/CONTRATO_SENTINELA_v1.md
git mv CONTRATO_ARQUITETO_v1.md contracts/CONTRATO_ARQUITETO_v1.md
git mv CONTRATO_ANALISTA_v1.md contracts/CONTRATO_ANALISTA_v1.md
git mv CONTRATO_REGISTRADOR_v1.md contracts/CONTRATO_REGISTRADOR_v1.md
git mv CONTRATO_ROLLBACK_v1.md contracts/CONTRATO_ROLLBACK_v1.md
git mv _BASE/CANONIZACOES/*.md canonizations/
