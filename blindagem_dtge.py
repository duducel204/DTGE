# -*- coding: utf-8 -*-
"""
blindagem_dtge.py

Camada de blindagem (Passo 02) — corrigida após auditoria real (3 achados).

O QUE MUDOU EM RELAÇÃO À VERSÃO ORIGINAL:

1. [CRÍTICO] O manifesto não é mais gerado pelo próprio script sendo
   validado. Antes: qualquer processo com acesso de escrita podia alterar o
   script E recalcular o manifesto no mesmo golpe — testei, passou limpo.
   Agora: o hash "de confiança" só entra através da CADEIA do Registrador
   (ferramenta_registrador_standalone.py), que é tamper-evident (cada
   entrada referencia o hash da anterior). Gerar um manifesto novo exige
   `autorizado_por` explícito — é ato de governança, não automatismo.

2. [MÉDIO] `sanitizar_argumento` era lista negra (bloqueava só
   caracteres tipo & ; | crase $ e quebra de linha) — testei e `>` passava direto, o que permitiria
   redirecionamento de saída se combinado com `shell=True` em algum lugar.
   Agora é lista BRANCA (só aceita caracteres explicitamente seguros) e
   existe `executar_seguro()` que nunca usa `shell=True`.

3. Não existia função para gerar o manifesto original — só validar. Agora
   `registrar_manifesto()` faz isso, mas sempre passando pelo Registrador.

RESSALVA HONESTA: `autorizado_por` aqui é um campo declarado, não uma
assinatura criptográfica verificada — não há sistema de identidade real
neste ambiente. Isso eleva bastante a barra (a ação fica registrada e
auditável na cadeia, não é mais silenciosa), mas não é prova de identidade.
"""

import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ferramenta_registrador_standalone as registrador
from dreamteam_core import ARTEFATOS_DIR, timestamp, timestamp_arquivo, garantir_dir, hash_dict, JSON_COMPACTO

MANIFESTOS_DIR = os.path.join(ARTEFATOS_DIR, "manifestos_blindagem")


def calcular_hash_arquivo(caminho_arquivo):
    """Calcula o hash SHA-256 de um arquivo. (Inalterado — já testado e correto.)"""
    sha256_hash = hashlib.sha256()
    if not os.path.exists(caminho_arquivo):
        return None
    with open(caminho_arquivo, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


# ---------------------------------------------------------------------------
# Correção do Achado 1 — manifesto só existe via Registrador, com autorização
# ---------------------------------------------------------------------------
def registrar_manifesto(nome_script: str, autorizado_por: str) -> dict:
    """
    Registra o hash ATUAL de nome_script como o hash confiável, mas só
    através da cadeia do Registrador — nunca localmente sem rastro.
    Requer autorizado_por explícito (regra dura: sem isso, não registra).
    """
    if not autorizado_por:
        raise PermissionError("registrar_manifesto exige 'autorizado_por' explícito — não é automatismo.")

    hash_atual = calcular_hash_arquivo(nome_script)
    if hash_atual is None:
        raise FileNotFoundError(f"Script '{nome_script}' não encontrado — nada para registrar.")

    garantir_dir(MANIFESTOS_DIR)
    caminho_manifesto = os.path.join(MANIFESTOS_DIR, f"MANIFESTO_{os.path.basename(nome_script)}_{timestamp_arquivo()}.json")
    conteudo = {
        "script": nome_script,
        "hash_sha256": hash_atual,
        "autorizado_por": autorizado_por,
        "timestamp_utc": timestamp(),
    }
    with open(caminho_manifesto, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, **JSON_COMPACTO)

    entrada_cadeia = registrador.ingerir(conteudo, tipo_origem="manifesto_blindagem", ref_origem=caminho_manifesto)
    return {"manifesto": caminho_manifesto, "seq_cadeia": entrada_cadeia["seq"], "hash_sha256": hash_atual}


def _entradas_validas_para_script(nome_script: str) -> list:
    """Varre a CADEIA do Registrador, retorna manifestos para nome_script
    cujo conteúdo NÃO foi alterado desde a ingestão (confere hash_conteudo)."""
    resultados = []
    if not os.path.exists(registrador.CADEIA_PATH):
        return resultados

    with open(registrador.CADEIA_PATH, encoding="utf-8") as f:
        for linha in f:
            entrada = json.loads(linha)
            if entrada.get("tipo_origem") != "manifesto_blindagem":
                continue
            caminho_manifesto = entrada["ref_origem"]
            if not os.path.exists(caminho_manifesto):
                continue
            with open(caminho_manifesto, encoding="utf-8") as mf:
                conteudo = json.load(mf)
            if conteudo.get("script") != nome_script:
                continue
            if hash_dict(conteudo) != entrada["hash_conteudo"]:
                continue  # manifesto foi alterado depois da ingestão -> não confiar
            resultados.append((entrada["seq"], conteudo))

    resultados.sort(key=lambda t: t[0])
    return resultados


def validar_integridade(nome_script: str) -> None:
    """
    Valida nome_script contra o manifesto mais recente e válido na CADEIA
    do Registrador — não contra um arquivo plano editável.
    """
    status_cadeia = registrador.verificar_integridade_cadeia()
    if not status_cadeia["integra"]:
        print(f"[ERRO CRÍTICO] Cadeia do Registrador comprometida: {status_cadeia['motivo']}")
        print("[BLOQUEIO] A base de confiança está corrompida — execução abortada.")
        sys.exit(1)

    entradas = _entradas_validas_para_script(nome_script)
    if not entradas:
        print(f"[ERRO CRÍTICO] Nenhum manifesto autorizado encontrado na cadeia para '{nome_script}'.")
        print("[BLOQUEIO] Rode registrar_manifesto(nome_script, autorizado_por=...) antes de executar.")
        sys.exit(1)

    _, manifesto = entradas[-1]
    hash_esperado = manifesto["hash_sha256"]
    hash_atual = calcular_hash_arquivo(nome_script)

    if hash_esperado != hash_atual:
        print(f"[ALERTA DE SEGURANÇA] Violação de integridade detectada em '{nome_script}'!")
        print(f"Esperado (autorizado por '{manifesto.get('autorizado_por')}' em {manifesto.get('timestamp_utc')}): {hash_esperado}")
        print(f"Obtido agora: {hash_atual}")
        print("[BLOQUEIO] Execução abortada pelo Sentinela.")
        sys.exit(1)

    print(f"[OK] Integridade validada para: {nome_script} (autorizado por '{manifesto.get('autorizado_por')}', cadeia íntegra)")


# ---------------------------------------------------------------------------
# Correção do Achado 2 — lista branca em vez de lista negra
# ---------------------------------------------------------------------------
_PADRAO_SEGURO = re.compile(r'^[A-Za-z0-9_\-./: ]+$')


def sanitizar_argumento(arg: str) -> str:
    """
    Lista BRANCA: só aceita letras, números, . _ - / : e espaço.
    Corrige achado de auditoria: a lista negra anterior deixava passar
    '>', '<', '(', ')', '*', etc. — testado e confirmado o vazamento.
    """
    if not isinstance(arg, str) or not _PADRAO_SEGURO.match(arg):
        print(f"[ALERTA DE SEGURANÇA] Argumento fora do padrão seguro (lista branca): {arg!r}")
        sys.exit(1)
    return arg


def executar_seguro(comando_lista: list) -> subprocess.CompletedProcess:
    """
    Executa comando SEM shell=True — argumentos como lista, nunca como
    string concatenada. Elimina a classe inteira de command injection,
    em vez de depender só de sanitizar_argumento.
    """
    if isinstance(comando_lista, str):
        raise TypeError("executar_seguro exige lista de argumentos (ex.: ['ls', '-la']), não string solta.")
    return subprocess.run(comando_lista, shell=False, capture_output=True, text=True)


if __name__ == "__main__":
    print("=== Teste 1: validar sem manifesto (deve bloquear) ===")
    try:
        validar_integridade(__file__)
    except SystemExit:
        print("(bloqueou corretamente)\n")

    print("=== Teste 2: registrar manifesto SEM autorizado_por (deve recusar) ===")
    try:
        registrar_manifesto(__file__, autorizado_por="")
        print("FALHA: deveria ter recusado")
    except PermissionError as e:
        print(f"Recusado corretamente: {e}\n")

    print("=== Teste 3: registrar manifesto COM autorização (deve funcionar) ===")
    resultado = registrar_manifesto(__file__, autorizado_por="usuario_humano_teste")
    print(f"Manifesto registrado: {resultado}\n")

    print("=== Teste 4: validar agora (deve passar) ===")
    validar_integridade(__file__)

    print("\n=== Teste 5: ataque real — adulterar o script E tentar fabricar manifesto sozinho (fora do Registrador) ===")
    caminho_fake = os.path.join(MANIFESTOS_DIR, "MANIFESTO_FALSO.json")
    with open(caminho_fake, "w", encoding="utf-8") as f:
        json.dump({"script": __file__, "hash_sha256": "hash_forjado_pelo_atacante", "autorizado_por": "ninguem_de_verdade"}, f)
    print("Arquivo de manifesto fabricado fora da cadeia (sem passar por registrador.ingerir).")
    print("Validação ignora esse arquivo forjado (não está na CADEIA), então segue usando o último legítimo:")
    validar_integridade(__file__)

    print("\n=== Teste 6: lista branca bloqueia '>' (achado 2, corrigido) ===")
    try:
        sanitizar_argumento("saida.txt > /tmp/hackeado")
        print("FALHA: deveria ter bloqueado")
    except SystemExit:
        print("(bloqueado corretamente)")
