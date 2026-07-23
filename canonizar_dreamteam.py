# -*- coding: utf-8 -*-
"""
canonizar_dreamteam.py

Executa TOOL-CMD-008 (congelar/encerrar) para os 5 contratos que estavam em
simulação e foram aprovados pelo humano ("Analisei os contratos simulados,
eles estão de acordo. Podemos seguir com a canonização de todos.").

Regra dura do catálogo (Seção D, TOOL-CMD-008):
"canonização só existe como arquivo em _BASE/CANONIZACOES/ + referência em
evento" / "Saída mínima: DECIDIR + artefato de canonização + hash."

Passos:
1. Promove cada contrato simulado a contrato real (remove marcações "(SIMULADO)"/"-SIM").
2. Gera hash de cada contrato real (reaproveita gerar_hash_sha256 do Orquestrador).
3. Cria artefato de canonização em _BASE/CANONIZACOES/ para cada agente.
4. Gera UM evento DECIDIR (batch) referenciando as 5 canonizações — evita
   fragmentar em 5 eventos redundantes (mesmo princípio de redução de
   tokens já aplicado: 1 registro compacto cobre o lote todo).
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ferramenta_orquestrador_standalone import gerar_hash_sha256, gerar_evento, _timestamp  # reaproveita infraestrutura existente

SIMULADO_DIR = "simulacao_dreamteam"
BASE_CANON_DIR = os.path.join("_BASE", "CANONIZACOES")

AGENTES = {
    "SENTINELA": {
        "arquivo_sim": "CONTRATO_SENTINELA_v1_(simulado).md",
        "arquivo_real": "CONTRATO_SENTINELA_v1.md",
        "id_sim": "CONTRATO-SEN-001-SIM",
        "id_real": "CONTRATO-SEN-001",
    },
    "ARQUITETO": {
        "arquivo_sim": "CONTRATO_ARQUITETO_v1_(simulado).md",
        "arquivo_real": "CONTRATO_ARQUITETO_v1.md",
        "id_sim": "CONTRATO-ARQ-001-SIM",
        "id_real": "CONTRATO-ARQ-001",
    },
    "ANALISTA": {
        "arquivo_sim": "CONTRATO_ANALISTA_v1_(simulado).md",
        "arquivo_real": "CONTRATO_ANALISTA_v1.md",
        "id_sim": "CONTRATO-ANA-001-SIM",
        "id_real": "CONTRATO-ANA-001",
    },
    "REGISTRADOR": {
        "arquivo_sim": "CONTRATO_REGISTRADOR_v1_(simulado).md",
        "arquivo_real": "CONTRATO_REGISTRADOR_v1.md",
        "id_sim": "CONTRATO-REG-001-SIM",
        "id_real": "CONTRATO-REG-001",
    },
    "ROLLBACK": {
        "arquivo_sim": "CONTRATO_ROLLBACK_v1_(simulado).md",
        "arquivo_real": "CONTRATO_ROLLBACK_v1.md",
        "id_sim": "CONTRATO-ROLLBACK-001-SIM",
        "id_real": "CONTRATO-ROLLBACK-001",
    },
}


def _promover_contrato(nome_agente: str, info: dict) -> str:
    """Remove marcações de simulação e escreve o contrato real."""
    caminho_sim = os.path.join(SIMULADO_DIR, info["arquivo_sim"])
    with open(caminho_sim, "r", encoding="utf-8") as f:
        conteudo = f.read()

    conteudo = conteudo.replace(" (SIMULADO)", "")
    conteudo = conteudo.replace(info["id_sim"], info["id_real"])
    conteudo = re.sub(
        r"(# CONTRATO_v1) — Agente",
        r"\1 — Agente",
        conteudo,
    )
    conteudo += f"\n\n---\n**Canonizado em (UTC):** {_timestamp()}\n**Promovido de:** `{info['id_sim']}` (simulação analisada e aprovada pelo humano)\n"

    with open(info["arquivo_real"], "w", encoding="utf-8") as f:
        f.write(conteudo)

    return info["arquivo_real"]


def _criar_artefato_canonizacao(nome_agente: str, caminho_contrato: str, hash_hex: str) -> str:
    os.makedirs(BASE_CANON_DIR, exist_ok=True)
    caminho_canon = os.path.join(BASE_CANON_DIR, f"CANONIZACAO_{nome_agente}_v1.md")
    conteudo = f"""# Canonização — Agente {nome_agente.capitalize()}

**Timestamp (UTC):** {_timestamp()}
**Artefato canonizado:** {caminho_contrato}
**Hash SHA256:** {hash_hex}
**Base da aprovação:** análise humana confirmando conformidade do contrato
simulado ("Analisei os contratos simulados, eles estão de acordo.").
**Regra aplicada:** TOOL-CMD-008 (congelar/encerrar).
"""
    with open(caminho_canon, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return caminho_canon


def main():
    referencias_evidencia = []
    canonizacoes = []

    for nome_agente, info in AGENTES.items():
        caminho_contrato = _promover_contrato(nome_agente, info)
        caminho_hash = gerar_hash_sha256(caminho_contrato)
        with open(caminho_hash, encoding="utf-8") as f:
            hash_hex = f.read().strip()
        caminho_canon = _criar_artefato_canonizacao(nome_agente, caminho_contrato, hash_hex)

        referencias_evidencia.append({"artifact_id": caminho_contrato, "hash_sha256": hash_hex})
        canonizacoes.append(caminho_canon)
        print(f"[{nome_agente}] contrato real: {caminho_contrato} | hash: {hash_hex[:16]}... | canonização: {caminho_canon}")

    caminho_evento_decidir = gerar_evento(
        tipo="DECIDIR",
        payload={
            "decisao": "APROVAR_CANONIZACAO_LOTE",
            "agentes": list(AGENTES.keys()),
            "justificativa": "Contratos simulados analisados e confirmados pelo humano; promovidos a reais e canonizados em _BASE/CANONIZACOES/.",
            "evidence_references": referencias_evidencia,
        },
    )
    print(f"\nEvento DECIDIR (batch) gerado em: {caminho_evento_decidir}")
    print(f"Canonizações criadas: {canonizacoes}")


if __name__ == "__main__":
    main()
