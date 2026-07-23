# -*- coding: utf-8 -*-
"""
ferramenta_executor_standalone.py

Implementação real (não simulada) do agente Executor (TOOL-DT-EXE-001),
conforme CONTRATO_EXECUTOR_v1.md.

Escopo desta versão (Opção B, restrita): execução de comandos bash e
criação/edição de arquivo dentro do sandbox local — nada de rede/API externa.

Regras duras implementadas em código (não só em texto):
1. Só executa com token event_type == "TOOL-EVT-005" e decision ==
   "EXECUTION_AUTHORIZED". Token "SEGUIR" (ou qualquer outro) é recusado.
2. Pré-condições checadas antes de qualquer execução: contrato presente,
   pendências vazias, snapshot de pré-estado registrado.
3. Não escreve em nenhum "store canônico" — gera pedido_de_registro como
   artefato (Registrador ainda não existe nesta conversa — ver Seção 4 do
   contrato).
4. Toda execução (sucesso ou falha) gera evidência: log + hash + event_id.
5. Reutiliza o mesmo ledger (artefatos/INDICE.jsonl) já usado pelo
   Orquestrador — auditoria única para o Dream Team, não fragmentada por agente.
"""

import os
import json
import hashlib
import datetime
import subprocess
import secrets
from typing import Optional, List


ARTEFATOS_DIR = "artefatos"
EXECUCOES_DIR = os.path.join(ARTEFATOS_DIR, "execucoes")
PEDIDOS_REGISTRO_DIR = os.path.join(ARTEFATOS_DIR, "pedidos_registro")
INDICE_PATH = os.path.join(ARTEFATOS_DIR, "INDICE.jsonl")
CONTRATO_EXECUTOR_PATH = "CONTRATO_EXECUTOR_v1.md"

_JSON_COMPACTO = {"ensure_ascii": False, "separators": (",", ":")}


def _timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _timestamp_arquivo() -> str:
    """Timestamp com microssegundos + sufixo aleatório — usar em NOMES DE ARQUIVO."""
    ts_micro = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    return f"{ts_micro}_{secrets.token_hex(3)}"


def _garantir_dirs():
    os.makedirs(EXECUCOES_DIR, exist_ok=True)
    os.makedirs(PEDIDOS_REGISTRO_DIR, exist_ok=True)


def _hash_conteudo(conteudo: str) -> str:
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def _registrar_no_indice(tipo_registro: str, ref: str, extra: Optional[dict] = None):
    _garantir_dirs()
    linha = {"ts": _timestamp(), "tipo": tipo_registro, "ref": ref}
    if extra:
        linha.update(extra)
    with open(INDICE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(linha, **_JSON_COMPACTO) + "\n")


# ---------------------------------------------------------------------------
# Regra Dura 1 — validação de token (nunca aceitar SEGUIR como autorização)
# ---------------------------------------------------------------------------
class TokenInvalidoError(PermissionError):
    """Levantado quando um token não autoriza execução."""


def validar_token_autorizacao(token: dict) -> None:
    if not isinstance(token, dict):
        raise TokenInvalidoError("Token inválido: esperado dict com campos do evento.")

    event_type = token.get("event_type")
    event_name = token.get("event_name")
    decision = token.get("decision")

    if event_name == "SEGUIR" or event_type != "TOOL-EVT-005":
        raise TokenInvalidoError(
            f"Token recusado: '{event_type}/{event_name}' não autoriza execução. "
            f"Apenas TOOL-EVT-005/AUTORIZACAO_EXECUCAO é aceito (SEGUIR é cognitivo, não executivo)."
        )
    if decision != "EXECUTION_AUTHORIZED":
        raise TokenInvalidoError(f"Token recusado: decision='{decision}', esperado 'EXECUTION_AUTHORIZED'.")


# ---------------------------------------------------------------------------
# Regra Dura 2 — pré-condições
# ---------------------------------------------------------------------------
def verificar_pre_condicoes(pendencias: Optional[List[str]] = None,
                             contrato_path: str = CONTRATO_EXECUTOR_PATH) -> None:
    if not os.path.exists(contrato_path):
        raise FileNotFoundError(f"Contrato do Executor não encontrado em '{contrato_path}'. Execução bloqueada.")
    if pendencias:
        raise RuntimeError(f"Pendências ativas bloqueiam execução: {pendencias}")


def _snapshot_pre_estado(contexto: dict) -> str:
    _garantir_dirs()
    timestamp = _timestamp()
    ts_arquivo = _timestamp_arquivo()
    caminho = os.path.join(EXECUCOES_DIR, f"SNAPSHOT_{ts_arquivo}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({"timestamp_utc": timestamp, "contexto": contexto}, f, **_JSON_COMPACTO)
    _registrar_no_indice("SNAPSHOT", caminho)
    return caminho


# ---------------------------------------------------------------------------
# Regra Dura 3 — pedido_de_registro (Executor não escreve no store canônico)
# ---------------------------------------------------------------------------
def _gerar_pedido_registro(event_id: str, tipo_acao: str, resultado: dict) -> str:
    _garantir_dirs()
    timestamp = _timestamp()
    ts_arquivo = _timestamp_arquivo()
    caminho = os.path.join(PEDIDOS_REGISTRO_DIR, f"PEDIDO_{ts_arquivo}.json")
    pedido = {
        "timestamp_utc": timestamp,
        "event_id_autorizacao": event_id,
        "tipo_acao": tipo_acao,
        "resultado": resultado,
        "status_ingestao": "PENDENTE (Registrador real ainda não existe nesta conversa)",
    }
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(pedido, f, **_JSON_COMPACTO)
    _registrar_no_indice("PEDIDO_REGISTRO", caminho, extra={"event_id_autorizacao": event_id})
    return caminho


# ---------------------------------------------------------------------------
# Ações executáveis (escopo restrito — Opção B)
# ---------------------------------------------------------------------------
def executar_bash(token_autorizacao: dict, comando: str,
                   pendencias: Optional[List[str]] = None) -> dict:
    """
    Executa um comando bash no sandbox, SOMENTE se o token for válido.
    Gera snapshot de pré-estado, evidência de execução e pedido_de_registro.
    """
    validar_token_autorizacao(token_autorizacao)
    verificar_pre_condicoes(pendencias)

    _snapshot_pre_estado({"acao": "executar_bash", "comando": comando})

    resultado_proc = subprocess.run(comando, shell=True, capture_output=True, text=True)
    resultado = {
        "comando": comando,
        "returncode": resultado_proc.returncode,
        "stdout": resultado_proc.stdout,
        "stderr": resultado_proc.stderr,
    }

    timestamp = _timestamp()
    ts_arquivo = _timestamp_arquivo()
    caminho_evidencia = os.path.join(EXECUCOES_DIR, f"EXEC_{ts_arquivo}.json")
    with open(caminho_evidencia, "w", encoding="utf-8") as f:
        json.dump(resultado, f, **_JSON_COMPACTO)

    hash_evidencia = _hash_conteudo(json.dumps(resultado, sort_keys=True))
    _registrar_no_indice(
        "EXECUCAO", caminho_evidencia,
        extra={
            "event_id": token_autorizacao.get("event_id"),
            "returncode": resultado_proc.returncode,
            "hash_resultado": hash_evidencia[:16],
        },
    )

    caminho_pedido = _gerar_pedido_registro(
        token_autorizacao.get("event_id", "N/A"), "executar_bash", resultado
    )

    return {
        "resultado": resultado,
        "evidencia": caminho_evidencia,
        "pedido_de_registro": caminho_pedido,
    }


def criar_arquivo_sandbox(token_autorizacao: dict, caminho_destino: str, conteudo: str,
                           pendencias: Optional[List[str]] = None) -> dict:
    """
    Cria/edita um arquivo no sandbox, SOMENTE se o token for válido.
    """
    validar_token_autorizacao(token_autorizacao)
    verificar_pre_condicoes(pendencias)

    _snapshot_pre_estado({"acao": "criar_arquivo_sandbox", "destino": caminho_destino})

    with open(caminho_destino, "w", encoding="utf-8") as f:
        f.write(conteudo)

    hash_arquivo = _hash_conteudo(conteudo)
    _registrar_no_indice(
        "EXECUCAO", caminho_destino,
        extra={"event_id": token_autorizacao.get("event_id"), "hash_arquivo": hash_arquivo[:16]},
    )

    caminho_pedido = _gerar_pedido_registro(
        token_autorizacao.get("event_id", "N/A"), "criar_arquivo_sandbox",
        {"caminho": caminho_destino, "hash_sha256": hash_arquivo},
    )

    return {"caminho": caminho_destino, "hash_sha256": hash_arquivo, "pedido_de_registro": caminho_pedido}


if __name__ == "__main__":
    print("=== Teste 1: token SEGUIR (deve ser RECUSADO) ===")
    token_seguir = {"event_type": "TOOL-EVT-002", "event_name": "SEGUIR", "decision": "N/A"}
    try:
        executar_bash(token_seguir, "echo 'isso nao deveria rodar'")
        print("FALHA DE SEGURANCA: execucao nao deveria ter ocorrido!")
    except TokenInvalidoError as e:
        print(f"Recusado corretamente: {e}")

    print("\n=== Teste 2: token AUTORIZACAO_EXECUCAO válido ===")
    token_valido = {
        "event_id": "EVT-AUTH-EXEC-TESTE-001",
        "event_type": "TOOL-EVT-005",
        "event_name": "AUTORIZACAO_EXECUCAO",
        "decision": "EXECUTION_AUTHORIZED",
        "justification": "Teste automatizado do Executor real.",
    }
    resultado = executar_bash(token_valido, "echo 'execucao real autorizada'")
    print(f"stdout capturado: {resultado['resultado']['stdout'].strip()}")
    print(f"evidencia em: {resultado['evidencia']}")
    print(f"pedido_de_registro em: {resultado['pedido_de_registro']}")

    print("\n=== Teste 3: token válido mas com pendência ativa (deve BLOQUEAR) ===")
    try:
        executar_bash(token_valido, "echo 'nao deveria rodar'", pendencias=["aguardando revisao X"])
        print("FALHA: deveria ter bloqueado por pendencia!")
    except RuntimeError as e:
        print(f"Bloqueado corretamente: {e}")

    print("\n=== Ledger (últimas linhas) ===")
    with open(INDICE_PATH, encoding="utf-8") as f:
        linhas = f.readlines()
    for linha in linhas[-6:]:
        print(" ", linha.strip())
