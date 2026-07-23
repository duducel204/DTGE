# -*- coding: utf-8 -*-
"""
ferramenta_registrador_standalone.py

Implementação do agente Registrador (TOOL-DT-REG-001), conforme
CONTRATO_REGISTRADOR_v1.md.

Regra dura: não decide, não opina, não executa — só registra. Registro é
sempre aditivo (nunca sobrescreve). Aqui isso é reforçado com uma CADEIA de
hash: cada entrada referencia o hash da entrada anterior, então qualquer
alteração retroativa quebra a cadeia de forma detectável (tamper-evident).

Também resolve a pendência deixada pelo Executor: varre
artefatos/pedidos_registro/ por pedidos ainda não ingeridos e os processa.
"""

import os
import json
import glob
from typing import Optional
from dreamteam_core import ARTEFATOS_DIR, timestamp, garantir_dir, hash_conteudo, registrar_no_indice, JSON_COMPACTO

REGISTRO_CANONICO_DIR = os.path.join(ARTEFATOS_DIR, "registro_canonico")
CADEIA_PATH = os.path.join(REGISTRO_CANONICO_DIR, "CADEIA.jsonl")
PEDIDOS_REGISTRO_DIR = os.path.join(ARTEFATOS_DIR, "pedidos_registro")
# Marcador de idempotência: separado do pedido original (que nunca é
# sobrescrito), evita reingestão duplicada se processar_pedidos_pendentes()
# for chamado mais de uma vez. Achado de auditoria corrigido.
PEDIDOS_INGERIDOS_PATH = os.path.join(REGISTRO_CANONICO_DIR, "PEDIDOS_INGERIDOS.jsonl")


def _ja_ingerido(caminho_pedido: str) -> bool:
    if not os.path.exists(PEDIDOS_INGERIDOS_PATH):
        return False
    with open(PEDIDOS_INGERIDOS_PATH, encoding="utf-8") as f:
        for linha in f:
            if json.loads(linha).get("pedido") == caminho_pedido:
                return True
    return False


def _marcar_ingerido(caminho_pedido: str, seq_cadeia: int):
    garantir_dir(REGISTRO_CANONICO_DIR)
    with open(PEDIDOS_INGERIDOS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"pedido": caminho_pedido, "seq_cadeia": seq_cadeia}, **JSON_COMPACTO) + "\n")


def _ultimo_hash_da_cadeia() -> str:
    if not os.path.exists(CADEIA_PATH):
        return "GENESIS"
    with open(CADEIA_PATH, encoding="utf-8") as f:
        linhas = f.readlines()
    if not linhas:
        return "GENESIS"
    return json.loads(linhas[-1])["hash_atual"]


def ingerir(conteudo_origem: dict, tipo_origem: str, ref_origem: str) -> dict:
    """
    Ingestão imutável e aditiva. NÃO valida mérito do conteúdo (isso não é
    papel do Registrador — regra dura). Só registra com integridade encadeada.
    """
    garantir_dir(REGISTRO_CANONICO_DIR)
    ts = timestamp()
    hash_anterior = _ultimo_hash_da_cadeia()
    seq = sum(1 for _ in open(CADEIA_PATH, encoding="utf-8")) + 1 if os.path.exists(CADEIA_PATH) else 1

    hash_conteudo_atual = hash_conteudo(json.dumps(conteudo_origem, sort_keys=True, ensure_ascii=False, default=str))
    hash_atual = hash_conteudo(f"{seq}|{ref_origem}|{hash_conteudo_atual}|{hash_anterior}")

    entrada = {
        "seq": seq,
        "ts": ts,
        "tipo_origem": tipo_origem,
        "ref_origem": ref_origem,
        "hash_conteudo": hash_conteudo_atual,
        "hash_anterior": hash_anterior,
        "hash_atual": hash_atual,
    }
    with open(CADEIA_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, **JSON_COMPACTO) + "\n")

    registrar_no_indice("INGESTAO_REGISTRADOR", ref_origem, extra={"seq": seq, "tipo_origem": tipo_origem, "hash_atual": hash_atual[:16]})
    return entrada


def processar_pedidos_pendentes() -> list:
    """
    Varre artefatos/pedidos_registro/*.json com status_ingestao PENDENTE
    (deixados pelo Executor) e ingere cada um na cadeia canônica. Não altera
    o arquivo original do pedido — o registro fica só na cadeia (aditivo).
    Idempotente: pedidos já ingeridos (marcados em PEDIDOS_INGERIDOS.jsonl)
    são pulados, mesmo que a função seja chamada múltiplas vezes.
    """
    if not os.path.isdir(PEDIDOS_REGISTRO_DIR):
        return []

    ingeridos = []
    for caminho in sorted(glob.glob(os.path.join(PEDIDOS_REGISTRO_DIR, "PEDIDO_*.json"))):
        if _ja_ingerido(caminho):
            continue
        with open(caminho, encoding="utf-8") as f:
            pedido = json.load(f)
        if "PENDENTE" not in pedido.get("status_ingestao", ""):
            continue
        entrada = ingerir(pedido, tipo_origem="pedido_de_registro_executor", ref_origem=caminho)
        _marcar_ingerido(caminho, entrada["seq"])
        ingeridos.append({"pedido": caminho, "seq_cadeia": entrada["seq"]})

    return ingeridos


def verificar_integridade_cadeia() -> dict:
    """Reconstrói a cadeia e confirma que nenhum elo foi violado."""
    if not os.path.exists(CADEIA_PATH):
        return {"integra": True, "motivo": "cadeia vazia"}

    hash_anterior_esperado = "GENESIS"
    with open(CADEIA_PATH, encoding="utf-8") as f:
        for i, linha in enumerate(f, start=1):
            entrada = json.loads(linha)
            if entrada["hash_anterior"] != hash_anterior_esperado:
                return {"integra": False, "motivo": f"quebra na seq={entrada['seq']}"}
            hash_recalculado = hash_conteudo(f"{entrada['seq']}|{entrada['ref_origem']}|{entrada['hash_conteudo']}|{entrada['hash_anterior']}")
            if hash_recalculado != entrada["hash_atual"]:
                return {"integra": False, "motivo": f"hash divergente na seq={entrada['seq']}"}
            hash_anterior_esperado = entrada["hash_atual"]

    return {"integra": True, "motivo": None}


if __name__ == "__main__":
    print("=== Teste 1: ingestão manual de um evento DECIDIR ===")
    entrada1 = ingerir({"tipo": "DECIDIR", "decisao": "exemplo"}, tipo_origem="evento", ref_origem="EXEMPLO_DECIDIR.json")
    print(entrada1)

    print("\n=== Teste 2: processar pedidos pendentes deixados pelo Executor ===")
    ingeridos = processar_pedidos_pendentes()
    print(f"{len(ingeridos)} pedido(s) ingerido(s): {ingeridos}")

    print("\n=== Teste 3: verificar integridade da cadeia ===")
    print(verificar_integridade_cadeia())

    print("\n=== Teste 5: rodar processar_pedidos_pendentes de novo (idempotência — não deve duplicar) ===")
    ingeridos_de_novo = processar_pedidos_pendentes()
    print(f"{len(ingeridos_de_novo)} pedido(s) ingerido(s) na 2a chamada (esperado: 0)")

    print("\n=== Teste 4: adulterar a cadeia manualmente e verificar de novo (deve detectar) ===")
    with open(CADEIA_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"seq": 999, "ts": "x", "tipo_origem": "adulterado", "ref_origem": "x",
                             "hash_conteudo": "x", "hash_anterior": "HASH_FALSO", "hash_atual": "x"}) + "\n")
    print(verificar_integridade_cadeia())
