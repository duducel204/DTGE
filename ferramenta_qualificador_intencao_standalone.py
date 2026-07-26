# -*- coding: utf-8 -*-
"""
ferramenta_qualificador_intencao_standalone.py — Agente 02_QUALIFICADOR_INTENCAO
Recebe intenções brutas → Qualifica estrutura → Passa para Orquestrador.
Integrado com dtge_logger para auditoria centralizada.
"""
import os
import json
import sys
from datetime import datetime, timedelta
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dtge_logger

ARTEFATOS_DIR = "artefatos"
INTENCOES_DIR = os.path.join(ARTEFATOS_DIR, "intencoes_qualificadas")
CACHE_DEDUP_PATH = os.path.join(ARTEFATOS_DIR, "cache_dedup_intencoes.jsonl")


def garantir_dirs():
    os.makedirs(INTENCOES_DIR, exist_ok=True)


def mapear_criticidade(texto_bruto: str) -> str:
    texto_lower = texto_bruto.lower()
    if any(palavra in texto_lower for palavra in ["rollback", "reverter", "desativar", "remover prod"]):
        return "CRITICA"
    if any(palavra in texto_lower for palavra in ["deploy", "produção", "prod", "ativar", "release"]):
        return "ALTA"
    if any(palavra in texto_lower for palavra in ["teste", "sandbox", "staging", "dev", "qualidade"]):
        return "MEDIA"
    return "BAIXA"


def mapear_tipo_intencao(texto_bruto: str) -> str:
    texto_lower = texto_bruto.lower()
    if any(palavra in texto_lower for palavra in ["deploy", "executar", "rodar", "ativar"]):
        return "EXECUCAO"
    if any(palavra in texto_lower for palavra in ["analisar", "verificar", "validar", "revisar", "auditar"]):
        return "ANALISE"
    if any(palavra in texto_lower for palavra in ["desenhar", "arquitetar", "planejar", "design"]):
        return "ARQUITETURA"
    return "EXECUCAO"


def verificar_loop_infinito(contexto_continuidade: dict):
    if not contexto_continuidade:
        return False, ""
    profundidade = contexto_continuidade.get("profundidade_ciclo", 0)
    if profundidade > 3:
        return True, f"Loop infinito detectado: profundidade {profundidade} > 3"
    return False, ""


def verificar_deduplicacao(texto_bruto: str, contexto_continuidade: dict):
    hash_intencao = hashlib.sha256(
        json.dumps({"texto": texto_bruto, "contexto": contexto_continuidade}, sort_keys=True).encode()
    ).hexdigest()[:12]

    agora = datetime.utcnow()
    limite_60s = agora - timedelta(seconds=60)

    garantir_dirs()

    if os.path.exists(CACHE_DEDUP_PATH):
        with open(CACHE_DEDUP_PATH, "r", encoding="utf-8") as f:
            for linha in f:
                try:
                    entry = json.loads(linha)
                    if entry["hash"] == hash_intencao:
                        ts_entry = datetime.fromisoformat(entry["ts"].replace("Z", "+00:00"))
                        if ts_entry > limite_60s:
                            return entry["id_intencao"], True
                except json.JSONDecodeError:
                    pass
    return None, False


def qualificar_intencao(intencao_bruta: dict) -> dict:
    garantir_dirs()
    texto_bruto = intencao_bruta.get("texto_bruto", "")
    usuario_origem = intencao_bruta.get("usuario_origem", "DESCONHECIDO")
    contexto_continuidade = intencao_bruta.get("contexto_continuidade", None)

    if not texto_bruto or len(texto_bruto.strip()) < 5:
        msg_erro = "Intenção muito vaga ou vazia"
        dtge_logger.registrar_log(
            agente="Qualificador",
            tipo_evento="ALERTA",
            mensagem=msg_erro,
            detalhes={"texto_bruto": texto_bruto},
        )
        return {"status": "REJEITADO", "motivo": msg_erro}

    bloqueado, motivo_bloqueio = verificar_loop_infinito(contexto_continuidade)
    if bloqueado:
        dtge_logger.registrar_log(
            agente="Qualificador",
            tipo_evento="ALERTA_INTEGRIDADE",
            mensagem=motivo_bloqueio,
        )
        return {"status": "BLOQUEADO", "motivo": motivo_bloqueio}

    id_existente, foi_encontrado = verificar_deduplicacao(texto_bruto, contexto_continuidade)
    if foi_encontrado:
        dtge_logger.registrar_log(
            agente="Qualificador",
            tipo_evento="SEGUIR",
            mensagem=f"Intenção duplicada (60s): reutilizando {id_existente}",
        )
        return {
            "status": "DEDUPLICADO",
            "id_intencao": id_existente,
            "motivo": "Intenção idêntica processada recentemente",
        }

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    criticidade = mapear_criticidade(texto_bruto)
    tipo_intencao = mapear_tipo_intencao(texto_bruto)
    id_intencao = f"INT-{tipo_intencao[:4]}-{ts}"

    profundidade_nova = (contexto_continuidade.get("profundidade_ciclo", 0) + 1) if contexto_continuidade else 0

    intencao_qualificada = {
        "id_intencao": id_intencao,
        "tipo": tipo_intencao,
        "criticidade": criticidade,
        "parametros": intencao_bruta.get("parametros", {}),
        "contexto_continuidade": {
            **(contexto_continuidade or {}),
            "profundidade_ciclo": profundidade_nova,
        },
        "usuario_origem": usuario_origem,
        "timestamp_criacao": ts,
    }

    nome_arquivo = f"{id_intencao}.json"
    caminho_intencao = os.path.join(INTENCOES_DIR, nome_arquivo)
    with open(caminho_intencao, "w", encoding="utf-8") as f:
        json.dump(intencao_qualificada, f, indent=2, ensure_ascii=False)

    hash_intencao = hashlib.sha256(
        json.dumps({"texto": texto_bruto, "contexto": contexto_continuidade}, sort_keys=True).encode()
    ).hexdigest()[:12]

    with open(CACHE_DEDUP_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": ts + "Z",
            "hash": hash_intencao,
            "id_intencao": id_intencao,
        }) + "\n")

    dtge_logger.registrar_log(
        agente="Qualificador",
        tipo_evento="DECIDIR",
        mensagem=f"Intenção qualificada: {id_intencao} ({tipo_intencao}, {criticidade})",
        detalhes={
            "id_intencao": id_intencao,
            "tipo": tipo_intencao,
            "criticidade": criticidade,
            "usuario": usuario_origem,
        },
        autorizado_por="SISTEMA",
    )

    hash_result = dtge_logger.registrar_hash_artefato(
        caminho_artefato=caminho_intencao,
        tipo_artefato="intencao_qualificada",
        autorizado_por="Qualificador",
    )

    return {
        "status": "SUCESSO",
        "id_intencao": id_intencao,
        "tipo": tipo_intencao,
        "criticidade": criticidade,
        "arquivo": caminho_intencao,
        "hash": hash_result["hash_sha256"],
    }


def main():
    """Teste com intenção bruta."""
    print("=== Qualificador Intenção: Teste ===\n")
    intencao_bruta = {
        "texto_bruto": "Fazer deploy da versão v1.2.3 para staging",
        "usuario_origem": "dev_team",
        "parametros": {"versao": "v1.2.3"},
    }
    print(f"Intenção bruta: {json.dumps(intencao_bruta, indent=2)}\n")
    resultado = qualificar_intencao(intencao_bruta)
    print(f"Resultado: {json.dumps(resultado, indent=2)}\n")


if __name__ == "__main__":
    main()
    
