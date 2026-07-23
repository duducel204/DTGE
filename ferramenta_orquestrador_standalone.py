# -*- coding: utf-8 -*-
"""
ferramenta_orquestrador_standalone.py

Versão adaptada de ferramenta_orquestrador.py para rodar SEM o framework
google.adk.tools (não disponível fora do sistema original).

Histórico de adaptação:
v1 - Removida dependência google.adk.tools; adicionados campos de ciclo do
     CONTRATO_v1.md (id_plano, tipo_plano, id_plano_pai, profundidade_ciclo);
     adicionadas funções de governança (eventos + evidência).
v2 - Registro automático de uso via decorator @registrar_uso (TOOL-EVD-001)
     em toda função-ferramenta.
v3 - Redução de consumo de tokens mantendo auditabilidade:
     (a) JSON compacto (sem indentação) nos arquivos de máquina;
     (b) log de uso guarda HASH dos argumentos, não os argumentos inteiros
         (o dado completo já existe no artefato gerado — não duplica);
     (c) ledger único artefatos/INDICE.jsonl: 1 linha compacta por registro,
         para auditoria/consulta sem abrir cada arquivo individualmente;
     (d) boilerplate fixo do contrato (Perguntas de Ancoragem) virou template
         referenciado por hash em vez de repetido por extenso a cada contrato.

Nenhuma regra de governança foi alterada — apenas o ambiente de execução e a
eficiência de armazenamento/leitura.
"""

import os
import json
import hashlib
import datetime
import functools
import secrets
from typing import List, Optional


ARTEFATOS_DIR = "artefatos"
EVENTOS_DIR = os.path.join(ARTEFATOS_DIR, "eventos")
EVIDENCIAS_DIR = os.path.join(ARTEFATOS_DIR, "evidencias")
TEMPLATES_DIR = os.path.join(ARTEFATOS_DIR, "_templates")
INDICE_PATH = os.path.join(ARTEFATOS_DIR, "INDICE.jsonl")

# JSON compacto: sem espaços/indentação. Continua 100% parseável e auditável
# (formatação não afeta integridade); só evita gastar tokens/bytes com
# espaçamento decorativo.
_JSON_COMPACTO = {"ensure_ascii": False, "separators": (",", ":")}


def _timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _timestamp_arquivo() -> str:
    """Timestamp com microssegundos + sufixo aleatório — usar em NOMES DE ARQUIVO.
    Corrige achado de auditoria: duas chamadas no mesmo segundo colidiam de
    nome e a segunda sobrescrevia a primeira silenciosamente."""
    ts_micro = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    return f"{ts_micro}_{secrets.token_hex(3)}"


def _garantir_dirs():
    os.makedirs(ARTEFATOS_DIR, exist_ok=True)
    os.makedirs(EVENTOS_DIR, exist_ok=True)
    os.makedirs(EVIDENCIAS_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def _hash_conteudo(conteudo: str) -> str:
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def _hash_dict(d: dict) -> str:
    """Hash determinístico de um dict (chaves ordenadas) — usado para provar
    quais argumentos geraram um artefato, sem precisar armazená-los de novo."""
    serial = json.dumps(d, sort_keys=True, ensure_ascii=False, default=str)
    return _hash_conteudo(serial)


def _registrar_no_indice(tipo_registro: str, ref: str, extra: Optional[dict] = None):
    """
    Ledger append-only (TOOL-EVD-001, formato compacto): 1 linha JSON por
    registro. É o ponto único de consulta para auditoria — evita precisar
    abrir cada arquivo individual para saber "o que aconteceu".
    """
    _garantir_dirs()
    linha = {
        "ts": _timestamp(),
        "tipo": tipo_registro,
        "ref": ref,
    }
    if extra:
        linha.update(extra)
    with open(INDICE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(linha, **_JSON_COMPACTO) + "\n")


# ---------------------------------------------------------------------------
# Instrumentação — registro automático de uso (TOOL-EVD-001)
#
# Regra do catálogo: "Se uma ferramenta for usada, seu uso deve gerar
# registro verificável." Aqui isso é feito sem duplicar dado: guardamos o
# HASH dos argumentos (prova de integridade / TOOL-EVD-002) em vez do
# conteúdo inteiro, já que o conteúdo completo já está no artefato gerado
# (contrato, evento etc.) e pode ser conferido cruzando o hash.
# ---------------------------------------------------------------------------
def registrar_uso(nome_ferramenta: str):
    """
    Decorator: gera evidência automática e compacta toda vez que a
    ferramenta decorada é chamada — sucesso ou falha. Não silencia exceções.
    """
    def decorador(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args_serializaveis = {
                **{f"arg_{i}": a for i, a in enumerate(args)},
                **kwargs,
            }
            hash_args = _hash_dict(args_serializaveis)
            try:
                resultado = func(*args, **kwargs)
                _registrar_no_indice(
                    "USO", nome_ferramenta,
                    extra={"status": "sucesso", "hash_args": hash_args[:16], "res": str(resultado)},
                )
                return resultado
            except Exception as e:
                _registrar_no_indice(
                    "USO", nome_ferramenta,
                    extra={"status": "falha", "hash_args": hash_args[:16], "erro": str(e)},
                )
                raise
        return wrapper
    return decorador


# ---------------------------------------------------------------------------
# Template de Perguntas de Ancoragem (TOOL-COG-007) — conteúdo fixo, gerado
# UMA vez e referenciado por hash em cada contrato, em vez de repetido por
# extenso a cada chamada. Reduz tokens sem perder auditabilidade: o hash
# garante que o texto referenciado é exatamente aquele, e qualquer alteração
# no template muda o hash (detectável).
# ---------------------------------------------------------------------------
_TEMPLATE_ANCORAGEM_ID = "TEMPLATE-COG-007-v1"
_TEMPLATE_ANCORAGEM_TEXTO = """## 5. Perguntas de Ancoragem (TOOL-COG-007)
- **O que valida o sucesso?** A conclusão de todos os critérios de aceite.
- **O que esta tarefa não é?** Não é uma autorização para alterar itens fora do escopo, nem uma execução (Orquestrador não executa — CONTRATO_v1.md, Seção 3).
- **Qual a evidência mínima de conclusão?** Um log de execução (TOOL-EVD-001) e o hash do artefato gerado (TOOL-EVD-002).
- **O que é reversível?** A ação deve ser acompanhada por um plano de rollback (TOOL-EVT-003).
"""


def _garantir_template_ancoragem() -> str:
    """Escreve o template em disco na primeira vez (idempotente) e retorna seu hash."""
    _garantir_dirs()
    caminho = os.path.join(TEMPLATES_DIR, f"{_TEMPLATE_ANCORAGEM_ID}.md")
    if not os.path.exists(caminho):
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(_TEMPLATE_ANCORAGEM_TEXTO)
    return _hash_conteudo(_TEMPLATE_ANCORAGEM_TEXTO)


# ---------------------------------------------------------------------------
# TOOL-ART-001 — Contrato (com campos de ciclo do CONTRATO_v1.md)
# ---------------------------------------------------------------------------
@registrar_uso("TOOL-ART-001:definir_escopo_e_gerar_contrato")
def definir_escopo_e_gerar_contrato(
    id_tarefa: str,
    objetivo: str,
    escopo_in: List[str],
    escopo_out: List[str],
    dod: List[str],
    pendencias: Optional[List[str]] = None,
    id_plano: Optional[str] = None,
    id_intencao_origem: Optional[str] = None,
    tipo_plano: Optional[str] = None,
    id_plano_pai: Optional[str] = None,
    profundidade_ciclo: int = 0,
) -> str:
    """
    Cria um artefato de Contrato / Plano de Ação (TOOL-ART-001).

    O texto fixo de "Perguntas de Ancoragem" não é repetido por extenso:
    o contrato referencia o template por ID + hash (ver _garantir_template_ancoragem).
    Retorna o caminho do arquivo .md gerado.
    """
    _garantir_dirs()
    timestamp = _timestamp()
    ts_arquivo = _timestamp_arquivo()
    id_plano = id_plano or f"PLANO-{id_tarefa}-{timestamp}"
    hash_template = _garantir_template_ancoragem()

    caminho_arquivo = os.path.join(ARTEFATOS_DIR, f"CONTRATO_{id_tarefa}_{ts_arquivo}.md")

    linhas_in = "\n".join(f"- {item}" for item in escopo_in) or "- (nenhum item declarado)"
    linhas_out = "\n".join(f"- {item}" for item in escopo_out) or "- (nenhum item declarado)"
    linhas_dod = "\n".join(f"- {item}" for item in dod) or "- (nenhum critério declarado)"
    linhas_pend = "\n".join(f"- {item}" for item in pendencias) if pendencias else "- Nenhuma pendência identificada."

    conteudo_md = f"""# Contrato / Plano de Ação: {id_tarefa} (TOOL-ART-001)

**Data de Geração (UTC):** {timestamp}

## 0. Rastreamento de Ciclo (CONTRATO_v1.md, Seção 2)
- id_plano: {id_plano}
- id_intencao_origem: {id_intencao_origem or "N/A"}
- tipo_plano: {tipo_plano or "N/A"}
- id_plano_pai: {id_plano_pai or "N/A"}
- profundidade_ciclo: {profundidade_ciclo}

## 1. Objetivo
{objetivo}

## 2. Escopo (TOOL-SEC-001)
### Dentro do Escopo:
{linhas_in}

### Fora do Escopo:
{linhas_out}

## 3. Critérios de Aceite (Definition of Done - DoD)
{linhas_dod}

## 4. Pendências (Pré-requisitos)
{linhas_pend}

Ref: {_TEMPLATE_ANCORAGEM_ID} (sha256:{hash_template[:16]}) — ver artefatos/_templates/
"""

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo_md)

    _registrar_no_indice("ARTEFATO", caminho_arquivo, extra={"id_plano": id_plano, "id_tarefa": id_tarefa})

    if profundidade_ciclo > 3:
        gerar_evento(
            tipo="ALERTA_INTEGRIDADE",
            payload={
                "causa": "RISCO_LOOP_INFINITO",
                "id_plano": id_plano,
                "profundidade_ciclo": profundidade_ciclo,
            },
        )

    return f"Contrato/Plano de Ação gerado com sucesso em: {caminho_arquivo}"


# ---------------------------------------------------------------------------
# TOOL-EVT-001..005 — Eventos de governança (genérico)
# Dono: humano para DECIDIR/SEGUIR/ROLLBACK/AUTORIZACAO_EXECUCAO;
#       sistema para ALERTA_INTEGRIDADE (nunca humano, TOOL-EVT-004).
# ---------------------------------------------------------------------------
TIPOS_EVENTO_HUMANO = {"DECIDIR", "SEGUIR", "ROLLBACK", "AUTORIZACAO_EXECUCAO"}
TIPOS_EVENTO_SISTEMA = {"ALERTA_INTEGRIDADE"}


@registrar_uso("TOOL-EVT:gerar_evento")
def gerar_evento(tipo: str, payload: dict, prev_ref: Optional[str] = None) -> str:
    """
    Gera um evento de governança (JSON compacto) conforme TOOL-EVT-001 a 005.

    tipo: um de DECIDIR, SEGUIR, ROLLBACK, ALERTA_INTEGRIDADE, AUTORIZACAO_EXECUCAO
    prev_ref: usado em ROLLBACK — regra dura: rollback não sobrescreve,
              encadeia por nova versão (TOOL-EVT-003).
    """
    if tipo not in TIPOS_EVENTO_HUMANO | TIPOS_EVENTO_SISTEMA:
        raise ValueError(f"Tipo de evento desconhecido: {tipo}")

    _garantir_dirs()
    timestamp = _timestamp()
    ts_arquivo = _timestamp_arquivo()
    dono = "sistema" if tipo in TIPOS_EVENTO_SISTEMA else "humano"

    evento = {
        "tipo": tipo,
        "dono": dono,
        "timestamp_utc": timestamp,
        "payload": payload,
    }
    if tipo == "ROLLBACK":
        evento["prev_ref"] = prev_ref

    caminho_arquivo = os.path.join(EVENTOS_DIR, f"{tipo}_{ts_arquivo}.json")
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(evento, f, **_JSON_COMPACTO)

    _registrar_no_indice("EVENTO", caminho_arquivo, extra={"evt_tipo": tipo, "dono": dono})

    return caminho_arquivo


# ---------------------------------------------------------------------------
# TOOL-EVD-001 — Log de evidência (TXT)
# ---------------------------------------------------------------------------
def gerar_log_evidencia(descricao: str, detalhes: Optional[dict] = None) -> str:
    _garantir_dirs()
    timestamp = _timestamp()
    ts_arquivo = _timestamp_arquivo()
    caminho_arquivo = os.path.join(EVIDENCIAS_DIR, f"LOG_{ts_arquivo}.txt")
    conteudo = f"[{timestamp}] {descricao}\n"
    if detalhes:
        conteudo += json.dumps(detalhes, **_JSON_COMPACTO) + "\n"
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo)
    _registrar_no_indice("LOG", caminho_arquivo)
    return caminho_arquivo


# ---------------------------------------------------------------------------
# TOOL-EVD-002 — Hash SHA256 (TXT)
# ---------------------------------------------------------------------------
@registrar_uso("TOOL-EVD-002:gerar_hash_sha256")
def gerar_hash_sha256(caminho_arquivo_alvo: str) -> str:
    """Gera arquivo .sha256.txt com o hash do arquivo alvo (prova de integridade)."""
    with open(caminho_arquivo_alvo, "rb") as f:
        conteudo = f.read()
    hash_hex = hashlib.sha256(conteudo).hexdigest()

    caminho_hash = f"{caminho_arquivo_alvo}.sha256.txt"
    with open(caminho_hash, "w", encoding="utf-8") as f:
        f.write(hash_hex)
    return caminho_hash


if __name__ == "__main__":
    caminho_contrato = definir_escopo_e_gerar_contrato(
        id_tarefa="TASK-EXEMPLO-001",
        objetivo="Validar a adaptação do Dream Team para o ambiente Claude.",
        escopo_in=["Gerar contrato de exemplo", "Gerar evento SEGUIR de exemplo"],
        escopo_out=["Executar qualquer ação real fora do sandbox"],
        dod=["Arquivo .md gerado", "Hash gerado", "Evento SEGUIR registrado"],
        tipo_plano="TESTE",
        profundidade_ciclo=0,
    )
    print(caminho_contrato)

    caminho_arquivo = caminho_contrato.split("em: ")[-1]
    caminho_hash = gerar_hash_sha256(caminho_arquivo)
    print(f"Hash gerado em: {caminho_hash}")

    caminho_evento = gerar_evento(tipo="SEGUIR", payload={"id_plano": "PLANO-TASK-EXEMPLO-001"})
    print(f"Evento SEGUIR gerado em: {caminho_evento}")

    print("\nLedger compacto (artefatos/INDICE.jsonl):")
    with open(INDICE_PATH, encoding="utf-8") as f:
        for linha in f:
            print(" ", linha.strip())
