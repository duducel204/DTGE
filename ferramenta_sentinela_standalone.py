# -*- coding: utf-8 -*-
"""
ferramenta_sentinela_standalone.py — Agente 02_SENTINELA

Recebe Plano de Ação → Audita riscos técnicos, estratégicos e cognitivos.
Integrado com dtge_logger para auditoria centralizada.
"""

import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dtge_logger

ARTEFATOS_DIR = "artefatos"
RISCOS_DIR = os.path.join(ARTEFATOS_DIR, "registros_riscos")

def garantir_dirs():
    os.makedirs(RISCOS_DIR, exist_ok=True)

def auditar_plano(plano: dict) -> dict:
    """
    Audita Plano de Ação contra riscos.
    
    Entrada: Plano de Ação (dict com id_plano, criticidade, profundidade_ciclo, etc)
    Saída: Registro de Riscos ou bloqueio
    """
    garantir_dirs()
    
    id_plano = plano.get("id_plano", "DESCONHECIDO")
    criticidade = plano.get("criticidade", "MEDIA")
    profundidade = plano.get("profundidade_ciclo", 0)
    requer_aprovacao = plano.get("requer_aprovacao_humana", False)
    
    riscos_encontrados = []
    bloqueado = False
    motivo_bloqueio = ""
    
    # Regra Dura 1: profundidade_ciclo > 3
    if profundidade > 3:
        riscos_encontrados.append({
            "tipo": "RISCO_LOOP_INFINITO",
            "severidade": "CRITICA",
            "descricao": f"Profundidade de ciclo ({profundidade}) excede limite seguro (3)",
        })
        bloqueado = True
        motivo_bloqueio = "Loop potencial detectado (profundidade > 3)"
    
    # Regra Dura 2: CRITICA sem aprovação humana
    if criticidade == "CRITICA" and not requer_aprovacao:
        riscos_encontrados.append({
            "tipo": "FALTA_APROVACAO_CRITICA",
            "severidade": "BLOQUEADOR",
            "descricao": "Plano CRITICA sem requisito de aprovação humana",
        })
        bloqueado = True
        motivo_bloqueio = "Plano crítico não possui aprovação humana requerida"
    
    # Regra de Negócio: Vieses cognitivos
    if len(plano.get("parametros", {})) > 10:
        riscos_encontrados.append({
            "tipo": "VIÉS_COMPLEXIDADE",
            "severidade": "MEDIA",
            "descricao": "Número elevado de parâmetros (> 10) pode indicar escopo ambíguo",
            "recomendacao": "Considerar subdivisão em planos menores",
        })
    
    # Registra no logger
    dtge_logger.registrar_log(
        agente="Sentinela",
        tipo_evento="SEGUIR" if not bloqueado else "ALERTA",
        mensagem=f"Auditoria de plano concluída: {id_plano} ({len(riscos_encontrados)} riscos encontrados)",
        detalhes={
            "id_plano": id_plano,
            "riscos_count": len(riscos_encontrados),
            "bloqueado": bloqueado,
        },
        autorizado_por="SISTEMA",
    )
    
    if bloqueado:
        dtge_logger.registrar_log(
            agente="Sentinela",
            tipo_evento="ALERTA_INTEGRIDADE",
            mensagem=f"Plano bloqueado: {motivo_bloqueio}",
            detalhes={"id_plano": id_plano, "motivo": motivo_bloqueio},
        )
        return {
            "status": "BLOQUEADO",
            "id_plano": id_plano,
            "motivo": motivo_bloqueio,
            "riscos": riscos_encontrados,
        }
    
    # Gera registro de riscos
    nome_arquivo = f"RISCOS_{id_plano}.json"
    caminho_riscos = os.path.join(RISCOS_DIR, nome_arquivo)
    
    registro_riscos = {
        "id_plano": id_plano,
        "riscos": riscos_encontrados,
        "status": "AUDITADO",
        "liberado_para": "ARQUITETO",
    }
    
    with open(caminho_riscos, "w", encoding="utf-8") as f:
        json.dump(registro_riscos, f, indent=2, ensure_ascii=False)
    
    # Registra hash
    hash_result = dtge_logger.registrar_hash_artefato(
        caminho_artefato=caminho_riscos,
        tipo_artefato="registro_riscos",
        autorizado_por="Sentinela",
    )
    
    return {
        "status": "APROVADO",
        "id_plano": id_plano,
        "riscos_encontrados": len(riscos_encontrados),
        "arquivo": caminho_riscos,
        "hash": hash_result["hash_sha256"],
    }

def main():
    """Teste com plano de exemplo."""
    print("=== Sentinela: Teste de Auditoria ===\n")
    
    plano_teste = {
        "id_plano": "PLANO-EXECUCAO-20260723T001122Z",
        "id_intencao_origem": "INT-DEPLOY-APP-STAGING",
        "tipo_plano": "EXECUCAO",
        "criticidade": "MEDIA",
        "parametros": {"versao_app": "v1.2.3"},
        "profundidade_ciclo": 1,
        "requer_aprovacao_humana": False,
        "status": "AGUARDANDO_SENTINELA",
    }
    
    print(f"Auditando: {json.dumps(plano_teste, indent=2)}\n")
    resultado = auditar_plano(plano_teste)
    print(f"Resultado: {json.dumps(resultado, indent=2)}\n")

if __name__ == "__main__":
    main()
