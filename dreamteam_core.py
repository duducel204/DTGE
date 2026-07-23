# -*- coding: utf-8 -*-
"""
dreamteam_core.py

Helpers compartilhados por todos os agentes do Dream Team (evita duplicar
timestamp/hash/ledger em cada arquivo de agente). Orquestrador e Executor já
entregues mantêm suas próprias cópias (não foram alterados, para não
quebrar o que já foi testado); os 5 agentes novos usam este núcleo.
"""

import os
import json
import hashlib
import datetime
import secrets

ARTEFATOS_DIR = "artefatos"
EVENTOS_DIR = os.path.join(ARTEFATOS_DIR, "eventos")
INDICE_PATH = os.path.join(ARTEFATOS_DIR, "INDICE.jsonl")

JSON_COMPACTO = {"ensure_ascii": False, "separators": (",", ":")}


def timestamp() -> str:
    """Timestamp em segundos — usar para o campo 'ts' do ledger (ordem cronológica, não precisa ser único)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def timestamp_arquivo() -> str:
    """
    Timestamp com microssegundos + sufixo aleatório — usar em NOMES DE ARQUIVO.
    Corrige achado de auditoria (TOOL-TECH-004): duas chamadas no mesmo
    segundo colidiam de nome e a segunda sobrescrevia a primeira
    silenciosamente (ex.: dois ALERTA_INTEGRIDADE do Sentinela no mesmo segundo).
    """
    ts_micro = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    return f"{ts_micro}_{secrets.token_hex(3)}"


def garantir_dir(caminho: str):
    os.makedirs(caminho, exist_ok=True)


def hash_conteudo(conteudo: str) -> str:
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def hash_dict(d: dict) -> str:
    return hash_conteudo(json.dumps(d, sort_keys=True, ensure_ascii=False, default=str))


def registrar_no_indice(tipo_registro: str, ref: str, extra: dict = None):
    """Ledger único e compartilhado (artefatos/INDICE.jsonl) — 1 linha compacta por registro."""
    garantir_dir(ARTEFATOS_DIR)
    linha = {"ts": timestamp(), "tipo": tipo_registro, "ref": ref}
    if extra:
        linha.update(extra)
    with open(INDICE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(linha, **JSON_COMPACTO) + "\n")
