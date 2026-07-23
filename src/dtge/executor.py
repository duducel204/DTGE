# -*- coding: utf-8 -*-
"""
ferramenta_executor_standalone.py

Implementação real (não simulada) do agente Executor (TOOL-DT-EXE-001),
conforme CONTRATO_EXECUTOR_v1.md.

Escopo desta versão (Opção B, restrita): execução de comandos bash e
criação/edição de arquivo dentro do sandbox local — nada de rede/API externa.

Regras duras implementadas em código (não só em texto):
1. Só executa com token event_type == "TOOL-EVT-005" e decision ==
   "EXECUTION_AUTHORIZED". Token "SEGUIR" (ou qualquer outro) é recusado.
2. Pré-condições checadas antes de qualquer execução: contrato presente,
   pendências vazias, snapshot de pré-estado registrado.
3. Não escreve em nenhum "store canônico" — gera pedido_de_registro como
   artefato (Registrador ainda não existe nesta conversa — ver Seção 4 do
   contrato).
4. Toda execução (sucesso ou falha) gera evidência: log + hash + event_id.
5. Reutiliza o mesmo ledger (artefatos/INDICE.jsonl) já usado pelo
   Orquestrador — auditoria única para o Dream Team, não fragmentada por agente.
"""

import os
import json
import hashlib
import datetime
import subprocess
import secrets
from typing import Optional, List


ARTEFATOS_DIR = "artefatos"
EXECUCOES_DIR = os.path.join(ARTEFATOS_DIR, "execucoes")
PEDIDOS_REGISTRO_DIR = os.path.join(ARTEFATOS_DIR, "pedidos_registro")
INDICE_PATH = os.path.join(ARTEFATOS_DIR, "INDICE.jsonl")
CONTRATO_EXECUTOR_PATH = "CONTRATO_EXECUTOR_v1.md"

_JSON_COMPACTO = {"ensure_ascii": False, "separators": (",", ":")}


def _timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _timestamp_arquivo() -> str:
    """Timestamp com microssegundos + sufixo aleatório — usar em NOMES DE ARQUIVO."""
    ts_micro = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    return f"{ts_micro}_{secrets.token_hex(3)}"


def _garantir_dirs():
    os.makedirs(EXECUCOES_DIR, exist_ok=True)
    os.makedirs(PEDIDOS_REGISTRO_DIR, exist_ok=True)


def _hash_conteudo(conteudo: str) -> str:
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def _registrar_no_indice(tipo_registro: str, ref: str, extra: Optional[dict] = None):
    _garantir_dirs()
    linha = {"ts": _timestamp(), "tipo": tipo_registro, "ref": ref}
    if extra:
        linha.update(extra)
    with open(INDICE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(linha, **_JSON_COMPACTO) + "\n")


# (rest of module omitted for brevity; full file available in original repo)
