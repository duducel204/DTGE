# -*- coding: utf-8 -*-
"""
ferramenta_sentinela_standalone.py

Implementação do agente Sentinela (TOOL-DT-SEN-001), conforme
CONTRATO_SENTINELA_v1.md.

Regra dura: Sentinela não decide, não executa — só identifica e registra.
Duas categorias de checagem:
1. Mecânica (determinística): profundidade_ciclo, repetição de chamada,
   criticidade sem aprovação humana exigida.
2. Cognitiva (TOOL-COG-002): fechamento precoce / confirmação / autoridade
   implícita — não são detectáveis de forma confiável por heurística pura,
   então a ferramenta estrutura e registra o julgamento (do humano ou de
   quem estiver rodando o pipeline), não o substitui.
"""

import os
import json
from typing import List, Optional
from dreamteam_core import (
    ARTEFATOS_DIR, timestamp, timestamp_arquivo, garantir_dir, hash_dict,
    registrar_no_indice, JSON_COMPACTO,
)

RISCOS_DIR = os.path.join(ARTEFATOS_DIR, "riscos")
HISTORICO_CHAMADAS_PATH = os.path.join(ARTEFATOS_DIR, "sentinela_historico_chamadas.jsonl")


def _checar_loop_infinito(plano: dict) -> Optional[dict]:
    """Regra dura do CONTRATO_ORQ_v1 replicada aqui como segunda linha de defesa:
    profundidade_ciclo > 3 OU repetição exata de (agente_destino, parametros)."""
    profundidade = plano.get("profundidade_ciclo", 0)
    if profundidade > 3:
        return {"causa": "RISCO_LOOP_INFINITO", "motivo": f"profundidade_ciclo={profundidade} > 3"}

    agente_destino = plano.get("agente_destino")
    parametros = plano.get("parametros", {})
    if agente_destino is None:
        return None

    garantir_dir(ARTEFATOS_DIR)
    chave = hash_dict({"agente_destino": agente_destino, "parametros": parametros})

    if os.path.exists(HISTORICO_CHAMADAS_PATH):
        with open(HISTORICO_CHAMADAS_PATH, encoding="utf-8") as f:
            for linha in f:
                if json.loads(linha).get("chave") == chave:
                    return {"causa": "RISCO_LOOP_INFINITO", "motivo": f"repetição exata de (agente_destino={agente_destino}, parametros)"}

    with open(HISTORICO_CHAMADAS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": timestamp(), "chave": chave}, **JSON_COMPACTO) + "\n")
    return None


def _checar_criticidade(plano: dict) -> Optional[str]:
    if plano.get("criticidade") == "CRITICA" and not plano.get("requisito_aprovacao_humana"):
        return "criticidade=CRITICA sem requisito_aprovacao_humana explícito no plano — bloqueado, devolver ao Orquestrador."
    return None


def auditar_plano(plano: dict) -> dict:
    """
    Auditoria mecânica do Plano de Ação. Retorna dict com:
    - bloqueado: bool
    - motivo: str | None
    - alerta: dict | None (ALERTA_INTEGRIDADE, se aplicável — TOOL-EVT-004)
    """
    alerta_loop = _checar_loop_infinito(plano)
    if alerta_loop:
        garantir_dir(ARTEFATOS_DIR)
        caminho_alerta = os.path.join(ARTEFATOS_DIR, "eventos", f"ALERTA_INTEGRIDADE_{timestamp_arquivo()}.json")
        garantir_dir(os.path.dirname(caminho_alerta))
        evento = {"tipo": "ALERTA_INTEGRIDADE", "dono": "sistema", "timestamp_utc": timestamp(), "payload": alerta_loop}
        with open(caminho_alerta, "w", encoding="utf-8") as f:
            json.dump(evento, f, **JSON_COMPACTO)
        registrar_no_indice("EVENTO", caminho_alerta, extra={"evt_tipo": "ALERTA_INTEGRIDADE", "dono": "sistema"})
        return {"bloqueado": True, "motivo": alerta_loop["motivo"], "alerta": caminho_alerta}

    motivo_criticidade = _checar_criticidade(plano)
    if motivo_criticidade:
        return {"bloqueado": True, "motivo": motivo_criticidade, "alerta": None}

    return {"bloqueado": False, "motivo": None, "alerta": None}


def registrar_riscos(id_plano: str, riscos: List[dict]) -> str:
    """
    Saída mínima do TOOL-DT-SEN-001: lista de riscos + mitigação proposta.
    Cada risco: {"tipo": "fechamento_precoce"|"confirmacao"|"autoridade_implicita"|"outro",
                 "descricao": str, "mitigacao": str}
    Não substitui julgamento humano — apenas estrutura e registra de forma auditável.
    """
    garantir_dir(RISCOS_DIR)
    ts = timestamp()
    ts_arquivo = timestamp_arquivo()
    caminho = os.path.join(RISCOS_DIR, f"RISCOS_{id_plano}_{ts_arquivo}.json")
    conteudo = {"id_plano": id_plano, "timestamp_utc": ts, "riscos": riscos}
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, **JSON_COMPACTO)
    registrar_no_indice("RISCOS", caminho, extra={"id_plano": id_plano, "qtd_riscos": len(riscos)})
    return caminho


if __name__ == "__main__":
    print("=== Teste 1: plano com profundidade_ciclo=4 (deve bloquear + ALERTA) ===")
    plano_loop = {"id_plano": "PLANO-TESTE-001", "profundidade_ciclo": 4, "criticidade": "BAIXA"}
    resultado = auditar_plano(plano_loop)
    print(resultado)

    print("\n=== Teste 2: plano CRITICA sem aprovação humana (deve bloquear) ===")
    plano_critico = {"id_plano": "PLANO-TESTE-002", "profundidade_ciclo": 0, "criticidade": "CRITICA"}
    print(auditar_plano(plano_critico))

    print("\n=== Teste 3: plano normal (deve passar) ===")
    plano_ok = {"id_plano": "PLANO-TESTE-003", "profundidade_ciclo": 1, "criticidade": "MEDIA",
                "agente_destino": "Arquiteto", "parametros": {"x": 1}}
    print(auditar_plano(plano_ok))

    print("\n=== Teste 4: repetição exata da mesma chamada (deve bloquear na 2a vez) ===")
    plano_repete = {"id_plano": "PLANO-TESTE-004", "profundidade_ciclo": 0, "criticidade": "BAIXA",
                     "agente_destino": "Analista", "parametros": {"y": 2}}
    print("1a chamada:", auditar_plano(plano_repete))
    print("2a chamada (repetida):", auditar_plano(plano_repete))

    print("\n=== Teste 5: registro de riscos cognitivos (TOOL-COG-002) ===")
    caminho_riscos = registrar_riscos("PLANO-TESTE-003", [
        {"tipo": "confirmacao", "descricao": "Plano assume que a opção B é a única viável sem checar alternativas.",
         "mitigacao": "Solicitar ao Analista comparação explícita de opções antes de prosseguir."},
    ])
    print(f"Riscos registrados em: {caminho_riscos}")
