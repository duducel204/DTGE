# -*- coding: utf-8 -*-
"""
dtge_logger.py

Sistema centralizado de logging para o Dream Team Governance Engine.
Todos os eventos, decisões e execuções são registrados em logs/DTGE_MASTER.log
com timestamp, agente, tipo de evento e hash de integridade.
"""

import os
import json
import hashlib
import datetime
from pathlib import Path

LOGS_DIR = "logs"
HASHES_DIR = "hashes"
MASTER_LOG = os.path.join(LOGS_DIR, "DTGE_MASTER.log")
HASHES_REGISTRY = os.path.join(HASHES_DIR, "HASHES_REGISTRY.jsonl")

JSON_COMPACTO = {"ensure_ascii": False, "separators": (",", ":")}


def garantir_dirs():
    """Cria diretórios de logs e hashes se não existirem."""
    Path(LOGS_DIR).mkdir(exist_ok=True)
    Path(HASHES_DIR).mkdir(exist_ok=True)


def timestamp() -> str:
    """Retorna timestamp em formato ISO com UTC."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def hash_conteudo(conteudo: str) -> str:
    """Calcula hash SHA-256 de um conteúdo."""
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def registrar_log(
    agente: str,
    tipo_evento: str,
    mensagem: str,
    detalhes: dict = None,
    autorizado_por: str = None,
) -> dict:
    """
    Registra um evento no log centralizado com integridade garantida.
    
    Args:
        agente: Nome do agente que gerou o evento
        tipo_evento: Tipo (ex: DECIDIR, SEGUIR, AUTORIZACAO_EXECUCAO, ALERTA, ERRO)
        mensagem: Descrição do evento
        detalhes: Dict opcional com dados adicionais
        autorizado_por: Quem autorizou (se aplicável)
    
    Returns:
        dict com metadados do registro (ts, seq, hash, etc)
    """
    garantir_dirs()
    
    ts = timestamp()
    seq = _obter_proxima_sequencia()
    
    entrada = {
        "seq": seq,
        "ts": ts,
        "agente": agente,
        "tipo": tipo_evento,
        "mensagem": mensagem,
    }
    
    if detalhes:
        entrada["detalhes"] = detalhes
    
    if autorizado_por:
        entrada["autorizado_por"] = autorizado_por
    
    # Hash da entrada (sem incluir o próprio hash)
    entrada_para_hash = json.dumps(entrada, sort_keys=True, ensure_ascii=False, default=str)
    entrada["hash"] = hash_conteudo(entrada_para_hash)
    
    # Escreve no log
    with open(MASTER_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, **JSON_COMPACTO) + "\n")
    
    return {
        "seq": seq,
        "ts": ts,
        "hash": entrada["hash"],
        "arquivo_log": MASTER_LOG,
    }


def registrar_hash_artefato(
    caminho_artefato: str,
    tipo_artefato: str,
    autorizado_por: str,
) -> dict:
    """
    Registra o hash de um artefato para auditoria e verificação de integridade.
    
    Args:
        caminho_artefato: Caminho do arquivo a verificar
        tipo_artefato: Tipo (ex: contrato, codigo, canonizacao)
        autorizado_por: Quem autorizou o artefato
    
    Returns:
        dict com hash e metadados
    """
    garantir_dirs()
    
    if not os.path.exists(caminho_artefato):
        raise FileNotFoundError(f"Artefato não encontrado: {caminho_artefato}")
    
    with open(caminho_artefato, "rb") as f:
        conteudo_bytes = f.read()
        hash_sha256 = hashlib.sha256(conteudo_bytes).hexdigest()
    
    ts = timestamp()
    
    registro = {
        "ts": ts,
        "arquivo": caminho_artefato,
        "tipo": tipo_artefato,
        "hash_sha256": hash_sha256,
        "tamanho_bytes": len(conteudo_bytes),
        "autorizado_por": autorizado_por,
    }
    
    # Registra no arquivo de hashes
    with open(HASHES_REGISTRY, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, **JSON_COMPACTO) + "\n")
    
    # Registra também no log
    registrar_log(
        agente="SISTEMA",
        tipo_evento="HASH_REGISTRADO",
        mensagem=f"Hash registrado para {tipo_artefato}: {caminho_artefato}",
        detalhes={
            "arquivo": caminho_artefato,
            "tipo": tipo_artefato,
            "hash": hash_sha256,
            "tamanho_bytes": len(conteudo_bytes),
        },
        autorizado_por=autorizado_por,
    )
    
    return {
        "arquivo": caminho_artefato,
        "hash_sha256": hash_sha256,
        "ts": ts,
        "registro_arquivo": HASHES_REGISTRY,
    }


def verificar_integridade_artefato(caminho_artefato: str, hash_esperado: str) -> bool:
    """
    Verifica se o hash atual de um artefato bate com o esperado.
    
    Args:
        caminho_artefato: Caminho do arquivo a verificar
        hash_esperado: Hash SHA-256 esperado
    
    Returns:
        True se integro, False caso contrário
    """
    if not os.path.exists(caminho_artefato):
        registrar_log(
            agente="SISTEMA",
            tipo_evento="ALERTA",
            mensagem=f"Arquivo não encontrado para verificação: {caminho_artefato}",
            detalhes={"arquivo": caminho_artefato},
        )
        return False
    
    with open(caminho_artefato, "rb") as f:
        hash_atual = hashlib.sha256(f.read()).hexdigest()
    
    integro = hash_atual == hash_esperado
    
    if not integro:
        registrar_log(
            agente="SISTEMA",
            tipo_evento="ALERTA_INTEGRIDADE",
            mensagem=f"Violação de integridade detectada em {caminho_artefato}",
            detalhes={
                "arquivo": caminho_artefato,
                "hash_esperado": hash_esperado,
                "hash_atual": hash_atual,
            },
        )
    
    return integro


def _obter_proxima_sequencia() -> int:
    """Obtém o próximo número de sequência do log."""
    garantir_dirs()
    
    if not os.path.exists(MASTER_LOG):
        return 1
    
    ultima_seq = 0
    with open(MASTER_LOG, "r", encoding="utf-8") as f:
        for linha in f:
            try:
                entrada = json.loads(linha)
                if "seq" in entrada:
                    ultima_seq = max(ultima_seq, entrada["seq"])
            except json.JSONDecodeError:
                pass
    
    return ultima_seq + 1


def listar_logs_agente(agente: str, limite: int = 50) -> list:
    """
    Lista os últimos logs de um agente específico.
    
    Args:
        agente: Nome do agente
        limite: Número máximo de entradas a retornar
    
    Returns:
        Lista de entradas de log ordenadas por sequência
    """
    garantir_dirs()
    
    if not os.path.exists(MASTER_LOG):
        return []
    
    entradas = []
    with open(MASTER_LOG, "r", encoding="utf-8") as f:
        for linha in f:
            try:
                entrada = json.loads(linha)
                if entrada.get("agente") == agente:
                    entradas.append(entrada)
            except json.JSONDecodeError:
                pass
    
    return entradas[-limite:]


def resumo_sistema() -> dict:
    """Retorna resumo do estado atual do sistema (logs, hashes, etc)."""
    garantir_dirs()
    
    total_logs = 0
    tipos_evento = {}
    agentes_ativos = set()
    
    if os.path.exists(MASTER_LOG):
        with open(MASTER_LOG, "r", encoding="utf-8") as f:
            for linha in f:
                try:
                    entrada = json.loads(linha)
                    total_logs += 1
                    tipo = entrada.get("tipo", "DESCONHECIDO")
                    tipos_evento[tipo] = tipos_evento.get(tipo, 0) + 1
                    agentes_ativos.add(entrada.get("agente", "DESCONHECIDO"))
                except json.JSONDecodeError:
                    pass
    
    total_hashes = 0
    if os.path.exists(HASHES_REGISTRY):
        with open(HASHES_REGISTRY, "r", encoding="utf-8") as f:
            total_hashes = sum(1 for _ in f)
    
    return {
        "total_logs": total_logs,
        "tipos_evento": tipos_evento,
        "agentes_ativos": sorted(list(agentes_ativos)),
        "total_hashes_registrados": total_hashes,
        "arquivo_log": MASTER_LOG,
        "arquivo_hashes": HASHES_REGISTRY,
    }


if __name__ == "__main__":
    print("=== Teste 1: Registrar log ===")
    resultado = registrar_log(
        agente="Orquestrador",
        tipo_evento="DECIDIR",
        mensagem="Inicializando sistema de governança",
        autorizado_por="CEO",
    )
    print(f"Log registrado: {resultado}\n")
    
    print("=== Teste 2: Registrar hash de um artefato ===")
    # Cria um artefato de teste
    artefato_teste = "artefato_teste.txt"
    with open(artefato_teste, "w") as f:
        f.write("Conteúdo de teste para hash")
    
    resultado_hash = registrar_hash_artefato(
        caminho_artefato=artefato_teste,
        tipo_artefato="teste",
        autorizado_por="CEO",
    )
    print(f"Hash registrado: {resultado_hash}\n")
    
    print("=== Teste 3: Verificar integridade ===")
    integro = verificar_integridade_artefato(
        caminho_artefato=artefato_teste,
        hash_esperado=resultado_hash["hash_sha256"],
    )
    print(f"Integridade OK: {integro}\n")
    
    print("=== Teste 4: Resumo do sistema ===")
    resumo = resumo_sistema()
    print(json.dumps(resumo, indent=2, ensure_ascii=False))
    
    # Limpeza
    os.remove(artefato_teste)
