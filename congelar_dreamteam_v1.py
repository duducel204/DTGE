# -*- coding: utf-8 -*-
"""
congelar_dreamteam_v1.py

Executa TOOL-CMD-008 (congelar/encerrar) sobre o estado FINAL e completo do
Dream Team nesta conversa: 7 contratos + 8 arquivos de código (núcleo +
7 agentes). Cobre as lacunas que a canonização anterior não cobriu
(Orquestrador e Executor não tinham canonização formal; código nunca tinha
sido canonizado, só os contratos).

Saída (regra dura TOOL-CMD-008): DECIDIR + artefato de canonização + hash,
para cada item, mais um evento DECIDIR final de congelamento do conjunto.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ferramenta_orquestrador_standalone import gerar_hash_sha256, gerar_evento, _timestamp

BASE_CANON_DIR = os.path.join("_BASE", "CANONIZACOES")

CONTRATOS_A_CANONIZAR = {
    "ORQUESTRADOR": "CONTRATO_ORQUESTRADOR_v1.md",
    "EXECUTOR": "CONTRATO_EXECUTOR_v1.md",
}

CODIGO_A_CANONIZAR = [
    "dreamteam_core.py",
    "ferramenta_orquestrador_standalone.py",
    "ferramenta_executor_standalone.py",
    "ferramenta_sentinela_standalone.py",
    "ferramenta_arquiteto_standalone.py",
    "ferramenta_analista_standalone.py",
    "ferramenta_registrador_standalone.py",
    "ferramenta_rollback_standalone.py",
]


def _criar_artefato_canonizacao(nome: str, caminho_alvo: str, hash_hex: str, categoria: str) -> str:
    os.makedirs(BASE_CANON_DIR, exist_ok=True)
    caminho_canon = os.path.join(BASE_CANON_DIR, f"CANONIZACAO_{nome}_v1.md")
    conteudo = f"""# Canonização — {nome} ({categoria})

**Timestamp (UTC):** {_timestamp()}
**Artefato canonizado:** {caminho_alvo}
**Hash SHA256:** {hash_hex}
**Regra aplicada:** TOOL-CMD-008 (congelar/encerrar).
**Status:** CONGELADO — esta é a versão de referência; qualquer alteração
futura no artefato exige nova canonização (nunca sobrescreve esta).
"""
    with open(caminho_canon, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return caminho_canon


def main():
    evidencias = []
    canonizacoes = []

    print("=== Canonizando contratos pendentes (Orquestrador, Executor) ===")
    for nome, caminho_contrato in CONTRATOS_A_CANONIZAR.items():
        caminho_hash = gerar_hash_sha256(caminho_contrato)
        with open(caminho_hash, encoding="utf-8") as f:
            hash_hex = f.read().strip()
        caminho_canon = _criar_artefato_canonizacao(nome, caminho_contrato, hash_hex, "contrato")
        evidencias.append({"artifact_id": caminho_contrato, "hash_sha256": hash_hex, "tipo": "contrato"})
        canonizacoes.append(caminho_canon)
        print(f"[{nome}] {caminho_contrato} | hash: {hash_hex[:16]}... | {caminho_canon}")

    print("\n=== Canonizando código (núcleo + 7 agentes) ===")
    for caminho_codigo in CODIGO_A_CANONIZAR:
        nome = "CODIGO_" + os.path.splitext(os.path.basename(caminho_codigo))[0].upper()
        caminho_hash = gerar_hash_sha256(caminho_codigo)
        with open(caminho_hash, encoding="utf-8") as f:
            hash_hex = f.read().strip()
        caminho_canon = _criar_artefato_canonizacao(nome, caminho_codigo, hash_hex, "código")
        evidencias.append({"artifact_id": caminho_codigo, "hash_sha256": hash_hex, "tipo": "codigo"})
        canonizacoes.append(caminho_canon)
        print(f"[{nome}] {caminho_codigo} | hash: {hash_hex[:16]}... | {caminho_canon}")

    print("\n=== Gerando DECIDIR final de congelamento ===")
    caminho_decidir = gerar_evento(
        tipo="DECIDIR",
        payload={
            "decisao": "CONGELAR_DREAMTEAM_v1",
            "descricao": "Congelamento formal do estado completo do Dream Team nesta conversa: "
                         "7 contratos (Orquestrador, Sentinela, Arquiteto, Analista, Executor, "
                         "Registrador, Rollback) + 8 arquivos de código (núcleo + 7 agentes), "
                         "todos com auditoria técnica prévia e correções aplicadas "
                         "(colisão de timestamp e idempotência do Registrador).",
            "total_itens_canonizados": len(evidencias),
            "evidence_references": evidencias,
        },
    )
    print(f"Evento DECIDIR (congelamento) gerado em: {caminho_decidir}")
    return caminho_decidir, canonizacoes, evidencias


if __name__ == "__main__":
    main()
