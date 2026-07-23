# -*- coding: utf-8 -*-
"""
ferramenta_orquestrador_standalone.py — Agente 03_ORQUESTRADOR

Recebe Intenção Qualificada → Gera Plano de Ação para o Sentinela.
Integrado com dtge_logger para auditoria centralizada.
"""

import os
import json
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dtge_logger

ARTEFATOS_DIR = "artefatos"
PLANOS_DIR = os.path.join(ARTEFATOS_DIR, "planos_acao")

def garantir_dirs():
    os.makedirs(PLANOS_DIR, exist_ok=True)

def processar_intencao_qualificada(intencao_obj: dict) -> dict:
    """
    Processa Intenção Qualificada e gera Plano de Ação.
    
    Entrada esperada:
    {
        "id_intencao": "INT-DEPLOY-APP-STAGING",
        "tipo": "EXECUCAO",
        "parametros": {"versao_app": "v1.2.3"},
        "criticidade": "MEDIA"
    }
    """
    garantir_dirs()
    
    id_intencao = intencao_obj.get("id_intencao", "DESCONHECIDO")
    tipo = intencao_obj.get("tipo", "DESCONHECIDO")
    criticidade = intencao_obj.get("criticidade", "MEDIA")
    parametros = intencao_obj.get("parametros", {})
    
    # Gera ID único do plano
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    id_plano = f"PLANO-{tipo}-{ts}"
    
    # Valida regras de negócio
    if criticidade == "CRITICA" and not intencao_obj.get("requer_aprovacao_humana", False):
        msg_alerta = f"Intenção CRITICA sem requisito de aprovação humana: {id_intencao}"
        dtge_logger.registrar_log(
            agente="Orquestrador",
            tipo_evento="ALERTA",
            mensagem=msg_alerta,
            detalhes={"id_intencao": id_intencao, "criticidade": criticidade},
        )
        return {"status": "BLOQUEADO", "motivo": msg_alerta}
    
    # Constrói Plano de Ação
    plano = {
        "id_plano": id_plano,
        "id_intencao_origem": id_intencao,
        "tipo_plano": tipo,
        "criticidade": criticidade,
        "parametros": parametros,
        "profundidade_ciclo": intencao_obj.get("profundidade_ciclo", 0),
        "requer_aprovacao_humana": criticidade == "CRITICA",
        "timestamp_criacao": ts,
        "status": "AGUARDANDO_SENTINELA",
    }
    
    # Salva o plano
    nome_arquivo = f"{id_plano}.json"
    caminho_plano = os.path.join(PLANOS_DIR, nome_arquivo)
    
    with open(caminho_plano, "w", encoding="utf-8") as f:
        json.dump(plano, f, indent=2, ensure_ascii=False)
    
    # Registra no logger
    resultado_log = dtge_logger.registrar_log(
        agente="Orquestrador",
        tipo_evento="DECIDIR",
        mensagem=f"Plano de Ação gerado para intenção: {id_intencao}",
        detalhes={
            "id_plano": id_plano,
            "id_intencao": id_intencao,
            "tipo": tipo,
            "criticidade": criticidade,
        },
        autorizado_por="SISTEMA",
    )
    
    # Registra hash do plano
    hash_result = dtge_logger.registrar_hash_artefato(
        caminho_artefato=caminho_plano,
        tipo_artefato="plano_acao",
        autorizado_por="Orquestrador",
    )
    
    return {
        "status": "SUCESSO",
        "id_plano": id_plano,
        "arquivo": caminho_plano,
        "log_seq": resultado_log["seq"],
        "hash": hash_result["hash_sha256"],
    }

def main():
    """Teste com intenção de exemplo."""
    print("=== Orquestrador: Teste de Processamento ===\n")
    
    intencao_teste = {
        "id_intencao": "INT-DEPLOY-APP-STAGING",
        "tipo": "EXECUCAO",
        "parametros": {"versao_app": "v1.2.3", "ambiente": "staging"},
        "criticidade": "MEDIA",
        "profundidade_ciclo": 0,
    }
    
    print(f"Processando: {json.dumps(intencao_teste, indent=2)}\n")
    resultado = processar_intencao_qualificada(intencao_teste)
    print(f"Resultado: {json.dumps(resultado, indent=2)}\n")
    
    # Resumo do sistema
    resumo = dtge_logger.resumo_sistema()
    print(f"Estado do sistema: {json.dumps(resumo, indent=2)}")

if __name__ == "__main__":
    main()
