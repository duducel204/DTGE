# -*- coding: utf-8 -*-
"""
ferramenta_arquiteto_standalone.py

Implementação do agente Arquiteto (TOOL-DT-ARQ-001), conforme
CONTRATO_ARQUITETO_v1.md.

Regra dura: não executa, não decide — projeta. Todo desenho deve incluir
rollback mínimo. Regra anti-drift: antes de propor componente novo, consulta
_BASE/CANONIZACOES/ e prioriza extensão sobre criação (RC-ASSIST-001).
"""

import os
from typing import List
from dreamteam_core import ARTEFATOS_DIR, timestamp, timestamp_arquivo, garantir_dir, registrar_no_indice

BASE_CANON_DIR = os.path.join("_BASE", "CANONIZACOES")


def _consultar_canonizacoes(termo_busca: str) -> List[str]:
    """Busca simples por palavra-chave nos títulos/arquivos já canonizados —
    checagem anti-drift antes de propor algo novo (RC-ASSIST-001: priorizar
    extensão sobre criação)."""
    if not os.path.isdir(BASE_CANON_DIR):
        return []
    encontrados = []
    termo = termo_busca.lower()
    for nome_arquivo in os.listdir(BASE_CANON_DIR):
        if termo in nome_arquivo.lower():
            encontrados.append(os.path.join(BASE_CANON_DIR, nome_arquivo))
    return encontrados


def modelar_arquitetura(
    id_tarefa: str,
    estados: List[str],
    dependencias: List[str],
    pontos_controle: List[str],
    rollback_esqueleto: str,
    componente_novo: str = None,
) -> dict:
    """
    Gera o artefato de arquitetura (MD): estados, dependências, pontos de
    controle, esqueleto de rollback. Se `componente_novo` for informado,
    roda a checagem anti-drift primeiro.
    """
    aviso_drift = None
    if componente_novo:
        achados = _consultar_canonizacoes(componente_novo)
        if achados:
            aviso_drift = (
                f"Possível desvio: já existe(m) canonização(ões) relacionadas a "
                f"'{componente_novo}': {achados}. Priorize extensão sobre criação (RC-ASSIST-001). "
                f"Apresentar Análise de Opções ao humano antes de prosseguir."
            )

    garantir_dir(ARTEFATOS_DIR)
    ts = timestamp()
    ts_arquivo = timestamp_arquivo()
    caminho = os.path.join(ARTEFATOS_DIR, f"ARQUITETURA_{id_tarefa}_{ts_arquivo}.md")

    linhas_estados = " → ".join(estados) if estados else "(nenhum estado definido)"
    linhas_dep = "\n".join(f"- {d}" for d in dependencias) or "- Nenhuma dependência declarada."
    linhas_pc = "\n".join(f"- {p}" for p in pontos_controle) or "- Nenhum ponto de controle declarado."

    conteudo = f"""# Arquitetura: {id_tarefa} (TOOL-DT-ARQ-001)

**Data de Geração (UTC):** {ts}

## Estados
{linhas_estados}

## Dependências
{linhas_dep}

## Pontos de Controle
{linhas_pc}

## Esqueleto de Rollback (obrigatório — TOOL-EVT-003)
{rollback_esqueleto}

## Checagem Anti-Drift
{aviso_drift or "Nenhum componente novo declarado, ou nenhuma canonização conflitante encontrada."}
"""
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)

    registrar_no_indice("ARQUITETURA", caminho, extra={"id_tarefa": id_tarefa, "aviso_drift": bool(aviso_drift)})

    return {"caminho": caminho, "aviso_drift": aviso_drift}


if __name__ == "__main__":
    print("=== Teste 1: arquitetura simples, sem componente novo ===")
    r1 = modelar_arquitetura(
        id_tarefa="TASK-ARQ-001",
        estados=["RECEBE_PLANO", "VALIDA", "MODELA", "ENTREGA_ANALISTA"],
        dependencias=["Plano de Ação do Orquestrador", "Registro de riscos do Sentinela"],
        pontos_controle=["Validar dependências antes de modelar", "Rollback esqueleto obrigatório"],
        rollback_esqueleto="Reverter para o estado anterior ao início da modelagem (nenhuma escrita persistente nesta fase).",
    )
    print(r1)

    print("\n=== Teste 2: componente novo que colide com canonização existente (deve avisar) ===")
    r2 = modelar_arquitetura(
        id_tarefa="TASK-ARQ-002",
        estados=["PROPOR", "VALIDAR"],
        dependencias=[],
        pontos_controle=["Checar anti-drift"],
        rollback_esqueleto="N/A nesta fase.",
        componente_novo="SENTINELA",
    )
    print(r2["aviso_drift"])
