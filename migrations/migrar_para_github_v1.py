# -*- coding: utf-8 -*-
"""
migrar_para_github_v1.py

Prepara a reorganização de repositório (ver PLANO_MIGRACAO_GITHUB_v1.md) de
forma segura: NÃO move nenhum arquivo sozinho (isso fica pro `git mv` real,
rodado por você). Este script só:
  1. Verifica integridade do que já existe (para antes de qualquer coisa se
     algo já estiver quebrado).
  2. Gera o mapeamento caminho-antigo -> caminho-novo.
  3. Gera uma canonização de SUCESSÃO por artefato (nunca apaga a original).
  4. Gera o evento DECIDIR formal autorizando a migração.
  5. Gera os comandos `git mv` reais, para você conferir e rodar.

IDEMPOTENTE: rodar --preparar mais de uma vez não duplica sucessões nem o
DECIDIR — cada chamada verifica o que já foi gerado antes de criar de novo.
"""

import argparse
import json
import os
import sys

# IMPORTANT: this script expects to be run from the REPO ROOT.
# It relies on importing modules that currently live in the repository root
# (before any git mv is executed). Therefore we add the current working
# directory to sys.path so imports resolve when the script is launched from
# the repo root:
#   # correto: from repo root
#   python3 migrations/migrar_para_github_v1.py --preparar
#   # errado: cd migrations && python3 migrar_para_github_v1.py --preparar
sys.path.insert(0, os.getcwd())

from ferramenta_orquestrador_standalone import gerar_hash_sha256, gerar_evento, _timestamp
import ferramenta_registrador_standalone as registrador
import token_autorizacao_dtge as token_dtge

BASE_CANON_DIR = os.path.join("_BASE", "CANONIZACOES")
MAPEAMENTO_PATH = "MAPEAMENTO_MIGRACAO_v1.json"
COMANDOS_GIT_PATH = "COMANDOS_GIT_MV.sh"

MAPEAMENTO_ARQUIVOS = {
    "dreamteam_core.py": "src/dtge/core.py",
    "ferramenta_orquestrador_standalone.py": "src/dtge/orquestrador.py",
    "ferramenta_executor_standalone.py": "src/dtge/executor.py",
    "ferramenta_sentinela_standalone.py": "src/dtge/sentinela.py",
    "ferramenta_arquiteto_standalone.py": "src/dtge/arquiteto.py",
    "ferramenta_analista_standalone.py": "src/dtge/analista.py",
    "ferramenta_registrador_standalone.py": "src/dtge/registrador.py",
    "ferramenta_rollback_standalone.py": "src/dtge/rollback.py",
    "token_autorizacao_dtge.py": "src/dtge/token_autorizacao.py",
    "CONTRATO_ORQUESTRADOR_v1.md": "contracts/CONTRATO_ORQUESTRADOR_v1.md",
    "CONTRATO_EXECUTOR_v1.md": "contracts/CONTRATO_EXECUTOR_v1.md",
    "CONTRATO_SENTINELA_v1.md": "contracts/CONTRATO_SENTINELA_v1.md",
    "CONTRATO_ARQUITETO_v1.md": "contracts/CONTRATO_ARQUITETO_v1.md",
    "CONTRATO_ANALISTA_v1.md": "contracts/CONTRATO_ANALISTA_v1.md",
    "CONTRATO_REGISTRADOR_v1.md": "contracts/CONTRATO_REGISTRADOR_v1.md",
    "CONTRATO_ROLLBACK_v1.md": "contracts/CONTRATO_ROLLBACK_v1.md",
}

# Lookup EXPLÍCITO (não adivinhado) das canonizações originais reais que já
# existem em _BASE/CANONIZACOES/ — conferido contra o `ls` real do diretório.
# token_autorizacao_dtge.py não tem canonização original: foi criado DEPOIS
# do congelamento v1 (congelar_dreamteam_v1.py rodou antes dele existir).
CANONIZACAO_ORIGINAL_LOOKUP = {
    "dreamteam_core.py": "CANONIZACAO_CODIGO_DREAMTEAM_CORE_v1.md",
    "ferramenta_orquestrador_standalone.py": "CANONIZACAO_CODIGO_FERRAMENTA_ORQUESTRADOR_STANDALONE_v1.md",
    "ferramenta_executor_standalone.py": "CANONIZACAO_CODIGO_FERRAMENTA_EXECUTOR_STANDALONE_v1.md",
    "ferramenta_sentinela_standalone.py": "CANONIZACAO_CODIGO_FERRAMENTA_SENTINELA_STANDALONE_v1.md",
    "ferramenta_arquiteto_standalone.py": "CANONIZACAO_CODIGO_FERRAMENTA_ARQUITETO_STANDALONE_v1.md",
    "ferramenta_analista_standalone.py": "CANONIZACAO_CODIGO_FERRAMENTA_ANALISTA_STANDALONE_v1.md",
    "ferramenta_registrador_standalone.py": "CANONIZACAO_CODIGO_FERRAMENTA_REGISTRADOR_STANDALONE_v1.md",
    "ferramenta_rollback_standalone.py": "CANONIZACAO_CODIGO_FERRAMENTA_ROLLBACK_STANDALONE_v1.md",
    "token_autorizacao_dtge.py": None,  # nunca canonizado — criado após o congelamento v1
    "CONTRATO_ORQUESTRADOR_v1.md": "CANONIZACAO_ORQUESTRADOR_v1.md",
    "CONTRATO_EXECUTOR_v1.md": "CANONIZACAO_EXECUTOR_v1.md",
    "CONTRATO_SENTINELA_v1.md": "CANONIZACAO_SENTINELA_v1.md",
    "CONTRATO_ARQUITETO_v1.md": "CANONIZACAO_ARQUITETO_v1.md",
    "CONTRATO_ANALISTA_v1.md": "CANONIZACAO_ANALISTA_v1.md",
    "CONTRATO_REGISTRADOR_v1.md": "CANONIZACAO_REGISTRADOR_v1.md",
    "CONTRATO_ROLLBACK_v1.md": "CANONIZACAO_ROLLBACK_v1.md",
}


def _verificar_estado_atual():
    """Passo 1: confere integridade de tudo ANTES de preparar qualquer migração."""
    print("=== Verificando integridade atual (antes de preparar migração) ===")
    problemas = []

    status_cadeia_reg = registrador.verificar_integridade_cadeia()
    if not status_cadeia_reg["integra"]:
        problemas.append(f"Cadeia do Registrador já está comprometida: {status_cadeia_reg['motivo']}")

    for caminho_antigo in MAPEAMENTO_ARQUIVOS:
        if not os.path.exists(caminho_antigo):
            problemas.append(f"Arquivo esperado não encontrado: {caminho_antigo}")

    if problemas:
        print("PARADO — resolva estes problemas antes de migrar:")
        for p in problemas:
            print(f"  - {p}")
        sys.exit(1)

    print("OK — nada quebrado antes de começar.\n")


def _ja_preparado():
    return os.path.exists(MAPEAMENTO_PATH)


def _gerar_sucessao_canonizacao(caminho_antigo, caminho_novo):
    """Gera canonização de SUCESSÃO — nunca apaga/sobrescreve a original.
    Chave de idempotência é o CAMINHO ANTIGO (único por definição), não um
    nome derivado — isso é o que corrige a colisão encontrada no teste real
    entre CONTRATO_ORQUESTRADOR e ferramenta_orquestrador."""
    os.makedirs(BASE_CANON_DIR, exist_ok=True)
    slug = caminho_antigo.replace("/", "_").replace(".", "_")
    caminho_sucessao = os.path.join(BASE_CANON_DIR, f"SUCESSAO_GITHUB_{slug}.md")

    if os.path.exists(caminho_sucessao):
        return caminho_sucessao  # idempotência: já gerada antes

    nome_original = CANONIZACAO_ORIGINAL_LOOKUP.get(caminho_antigo)
    caminho_original = os.path.join(BASE_CANON_DIR, nome_original) if nome_original else None
    original_existe = caminho_original and os.path.exists(caminho_original)

    hash_atual = None
    if os.path.exists(caminho_antigo):
        caminho_hash = gerar_hash_sha256(caminho_antigo)
        with open(caminho_hash, encoding="utf-8") as f:
            hash_atual = f.read().strip()

    conteudo = f"""# Canonização (SUCESSÃO) — {os.path.basename(caminho_antigo)}

**Timestamp (UTC):** {_timestamp()}
**Canonização original (nunca apagada):** {caminho_original if original_existe else "N/A — este artefato nunca foi canonizado antes (ex.: criado após o congelamento v1)"}
**Caminho antigo:** {caminho_antigo}
**Caminho novo (pós-migração GitHub):** {caminho_novo}
**Hash SHA256 (conteúdo não muda, só o local):** {hash_atual}
**Motivo:** reorganização de repositório (PLANO_MIGRACAO_GITHUB_v1.md).
**Regra aplicada:** suscensão nunca sobrescreve — mesma lógica do Rollback (TOOL-EVT-003).
"""
    with open(caminho_sucessao, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return caminho_sucessao


def preparar():
    _verificar_estado_atual()

    if _ja_preparado():
        print(f"Já existe {MAPEAMENTO_PATH} — preparação é idempotente, não vou gerar de novo.")
        print("Se quiser regenerar do zero, apague esse arquivo manualmente primeiro.")
        return

    print("=== Gerando sucessões de canonização (uma por artefato canonizado) ===")
    sucessoes = []
    for caminho_antigo, caminho_novo in MAPEAMENTO_ARQUIVOS.items():
        caminho_sucessao = _gerar_sucessao_canonizacao(caminho_antigo, caminho_novo)
        sucessoes.append(caminho_sucessao)
        print(f"  {caminho_antigo} -> {caminho_novo} | sucessão: {caminho_sucessao}")

    print("\n=== Gerando DECIDIR formal de autorização da migração ===")
    caminho_decidir = gerar_evento(
        tipo="DECIDIR",
        payload={
            "decisao": "AUTORIZAR_MIGRACAO_GITHUB_v1",
            "descricao": "Reorganização de repositório para layout src/dtge + contracts/ + canonizations/ + var/, "
                         "preservando todo o histórico via canonizações de sucessão (nunca sobrescreve).",
            "total_arquivos": len(MAPEAMENTO_ARQUIVOS),
            "sucessoes_geradas": sucessoes,
        },
    )
    print(f"DECIDIR gerado em: {caminho_decidir}")

    print("\n=== Gravando mapeamento ===")
    with open(MAPEAMENTO_PATH, "w", encoding="utf-8") as f:
        json.dump({"mapeamento": MAPEAMENTO_ARQUIVOS, "decidir_ref": caminho_decidir, "sucessoes": sucessoes}, f, indent=2, ensure_ascii=False)
    print(f"Mapeamento salvo em: {MAPEAMENTO_PATH}")

    print("\n=== Gerando comandos git mv ===")
    with open(COMANDOS_GIT_PATH, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\nset -e\n")
        f.write("mkdir -p src/dtge contracts canonizations var\n")
        for antigo, novo in MAPEAMENTO_ARQUIVOS.items():
            f.write(f"git mv {antigo} {novo}\n")
        f.write("git mv _BASE/CANONIZACOES/*.md canonizations/\n")
    print(f"Comandos gerados em: {COMANDOS_GIT_PATH} (confira antes de rodar!)")


def verificar():
    print("=== Verificação pós-migração ===")
    if not os.path.exists(MAPEAMENTO_PATH):
        print("Nenhum mapeamento encontrado — rode --preparar primeiro.")
        sys.exit(1)

    with open(MAPEAMENTO_PATH, encoding="utf-8") as f:
        dados = json.load(f)

    faltando = []
    for antigo, novo in dados["mapeamento"].items():
        if not os.path.exists(novo) and not os.path.exists(antigo):
            faltando.append((antigo, novo))

    if faltando:
        print("ATENÇÃO — arquivos não encontrados nem no caminho antigo nem no novo:")
        for antigo, novo in faltando:
            print(f"  {antigo} / {novo}")
    else:
        print("Todos os arquivos do mapeamento localizados (antigo ou novo caminho). Confira manualmente se o `git mv` já rodou.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preparar", action="store_true")
    parser.add_argument("--verificar", action="store_true")
    args = parser.parse_args()

    if args.preparar:
        preparar()
    elif args.verificar:
        verificar()
    else:
        print("Use --preparar ou --verificar")
