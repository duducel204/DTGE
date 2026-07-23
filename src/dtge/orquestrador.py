# -*- coding: utf-8 -*-
"""
ferramenta_orquestrador_standalone.py

Versão adaptada de ferramenta_orquestrador.py para rodar SEM o framework
google.adk.tools (não disponível fora do sistema original).

Histórico de adaptação:
v1 - Removida dependência google.adk.tools; adicionados campos de ciclo do
     CONTRATO_v1.md (id_plano, tipo_plano, id_plano_pai, profundidade_ciclo);
     adicionadas funções de governança (eventos + evidência).
v2 - Registro automático de uso via decorator @registrar_uso (TOOL-EVD-001)
     em toda função-ferramenta.
v3 - Redução de consumo de tokens mantendo auditabilidade:
     (a) JSON compacto (sem indentação) nos arquivos de máquina;
     (b) log de uso guarda HASH dos argumentos, não os argumentos inteiros
         (o dado completo já existe no artefato gerado — não duplica);
     (c) ledger único artefatos/INDICE.jsonl: 1 linha compacta por registro,
         para auditoria/consulta sem abrir cada arquivo individualmente;
     (d) boilerplate fixo do contrato (Perguntas de Ancoragem) virou template
         referenciado por hash em vez de repetido por extenso a cada contrato.

Nenhuma regra de governança foi alterada — apenas o ambiente de execução e a
eficiência de armazenamento/leitura.
"""

import os
import json
import hashlib
import datetime
import functools
import secrets
from typing import List, Optional


ARTEFATOS_DIR = "artefatos"
EVENTOS_DIR = os.path.join(ARTEFATOS_DIR, "eventos")
EVIDENCIAS_DIR = os.path.join(ARTEFATOS_DIR, "evidencias")
TEMPLATES_DIR = os.path.join(ARTEFATOS_DIR, "_templates")
INDICE_PATH = os.path.join(ARTEFATOS_DIR, "INDICE.jsonl")

# JSON compacto: sem espaços/indentação. Continua 100% parseável e auditável
# (formatação não afeta integridade); só evita gastar tokens/bytes com
# espaçamento decorativo.
_JSON_COMPACTO = {"ensure_ascii": False, "separators": (",", ":")}


def _timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _timestamp_arquivo() -> str:
    """Timestamp com microssegundos + sufixo aleatório — usar em NOMES DE ARQUIVO.
    Corrige achado de auditoria: duas chamadas no mesmo segundo colidiam de
    nome e a segunda sobrescrevia a primeira silenciosamente."""
    ts_micro = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    return f"{ts_micro}_{secrets.token_hex(3)}"


def _garantir_dirs():
    os.makedirs(ARTEFATOS_DIR, exist_ok=True)
    os.makedirs(EVENTOS_DIR, exist_ok=True)
    os.makedirs(EVIDENCIAS_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def _hash_conteudo(conteudo: str) -> str:
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def _hash_dict(d: dict) -> str:
    """Hash determinístico de um dict (chaves ordenadas) — usado para provar
    quais argumentos geraram um artefato, sem precisar armazená-los de novo."""
    serial = json.dumps(d, sort_keys=True, ensure_ascii=False, default=str)
    return _hash_conteudo(serial)


def _registrar_no_indice(tipo_registro: str, ref: str, extra: Optional[dict] = None):
    """
    Ledger append-only (TOOL-EVD-001, formato compacto): 1 linha JSON por
    registro. É o ponto único de consulta para auditoria — evita precisar
    abrir cada arquivo individual para saber "o que aconteceu".
    """
    _garantir_dirs()
    linha = {
        "ts": _timestamp(),
        "tipo": tipo_registro,
        "ref": ref,
    }
    if extra:
        linha.update(extra)
    with open(INDICE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(linha, **_JSON_COMPACTO) + "\n")


# ---------------------------------------------------------------------------
# Instrumentação — registro automático de uso (TOOL-EVD-001)
#
# Regra do catálogo: "Se uma ferramenta for usada, seu uso deve gerar
# registro verificável." Aqui isso é feito sem duplicar dado: guardamos o
# HASH dos argumentos (prova de integridade / TOOL-EVD-002) em vez do
# conteúdo inteiro, já que o conteúdo completo já está no artefato gerado
# (contrato, evento etc.) e pode ser conferido cruzando o hash.
# ---------------------------------------------------------------------------
def registrar_uso(nome_ferramenta: str):
    """
    Decorator: gera evidência automática e compacta toda vez que a
    ferramenta decorada é chamada — sucesso ou falha. Não silencia exceções.
    """
    def decorador(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args_serializaveis = {
                **{f"arg_{i}": a for i, a in enumerate(args)},
                **kwargs,
            }
            hash_args = _hash_dict(args_serializaveis)
            try:
                resultado = func(*args, **kwargs)
                _registrar_no_indice(
                    "USO", nome_ferramenta,
                    extra={"status": "sucesso", "hash_args": hash_args[:16], "res": str(resultado)},
                )
                return resultado
            except Exception as e:
                _registrar_no_indice(
                    "USO", nome_ferramenta,
                    extra={"status": "falha", "hash_args": hash_args[:16], "erro": str(e)},
                )
                raise
        return wrapper
    return decorador

# (rest of file omitted in this push for brevity — full module kept in original repo)
