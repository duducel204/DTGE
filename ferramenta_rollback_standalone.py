# -*- coding: utf-8 -*-
"""
ferramenta_rollback_standalone.py

Implementação do plano de Rollback (TOOL-EVT-003), conforme
CONTRATO_ROLLBACK_v1.md.

Regra dura: rollback NÃO sobrescreve — sempre cria nova versão encadeada
(prev_ref). Reaproveita gerar_evento do Orquestrador (mesma infraestrutura
de eventos, mesmo ledger) para não duplicar o formato de evento.
"""

import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ferramenta_orquestrador_standalone import gerar_evento  # reaproveita TOOL-EVT-003 já implementado
from dreamteam_core import ARTEFATOS_DIR, timestamp, garantir_dir, hash_conteudo, registrar_no_indice

VERSOES_DIR = os.path.join(ARTEFATOS_DIR, "versoes")


def executar_rollback(
    prev_ref: str,
    motivo: str,
    autorizado_por: str,
    caminho_alvo: Optional[str] = None,
    conteudo_versao_anterior: Optional[str] = None,
) -> dict:
    """
    Executa rollback: gera evento ROLLBACK (TOOL-EVT-003) encadeado a
    prev_ref, e — se caminho_alvo/conteudo_versao_anterior forem informados —
    escreve uma NOVA versão do artefato (nunca sobrescreve o original).

    autorizado_por: identificação de quem autorizou (regra: dono do evento
    ROLLBACK é humano — TIPOS_EVENTO_HUMANO no módulo do Orquestrador).
    """
    if not autorizado_por:
        raise PermissionError("Rollback requer 'autorizado_por' explícito (evento é de dono humano).")

    caminho_nova_versao = None
    if caminho_alvo and conteudo_versao_anterior is not None:
        garantir_dir(VERSOES_DIR)
        ts = timestamp()
        base_nome = os.path.basename(caminho_alvo)
        caminho_nova_versao = os.path.join(VERSOES_DIR, f"{base_nome}.rollback_{ts}")
        with open(caminho_nova_versao, "w", encoding="utf-8") as f:
            f.write(conteudo_versao_anterior)
        registrar_no_indice(
            "ROLLBACK_VERSAO", caminho_nova_versao,
            extra={"prev_ref": prev_ref, "hash_nova_versao": hash_conteudo(conteudo_versao_anterior)[:16]},
        )

    caminho_evento = gerar_evento(
        tipo="ROLLBACK",
        payload={
            "motivo": motivo,
            "autorizado_por": autorizado_por,
            "nova_versao": caminho_nova_versao,
        },
        prev_ref=prev_ref,
    )

    return {"evento_rollback": caminho_evento, "nova_versao": caminho_nova_versao}


if __name__ == "__main__":
    print("=== Teste 1: rollback sem autorizado_por (deve recusar) ===")
    try:
        executar_rollback(prev_ref="ARTEFATO-X-v1", motivo="teste", autorizado_por="")
        print("FALHA: deveria ter recusado.")
    except PermissionError as e:
        print(f"Recusado corretamente: {e}")

    print("\n=== Teste 2: rollback válido, com nova versão de arquivo ===")
    resultado = executar_rollback(
        prev_ref="CONTRATO_EXEMPLO_v2.md",
        motivo="Execução v2 falhou em validação pós-execução; revertendo para v1 conhecida.",
        autorizado_por="usuario_humano_teste",
        caminho_alvo="CONTRATO_EXEMPLO.md",
        conteudo_versao_anterior="# Conteúdo da versão anterior conhecida (v1)\n",
    )
    print(resultado)
