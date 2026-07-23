# -*- coding: utf-8 -*-
"""
ferramenta_analista_standalone.py

Implementação do agente Analista (TOOL-DT-ANA-001), conforme
CONTRATO_ANALISTA_v1.md.

Regra dura: não decide, não executa — recomenda com base em evidência.
A pontuação é determinística e transparente (não é "opinião" da IA) para
que a recomendação seja auditável: quem ler o artefato vê exatamente como
o Analista chegou naquela recomendação.
"""

import os
from typing import List, Dict
from dreamteam_core import ARTEFATOS_DIR, timestamp, timestamp_arquivo, garantir_dir, registrar_no_indice

_ESCALA = {"baixo": 1, "baixa": 1, "medio": 2, "média": 2, "medium": 2, "alto": 3, "alta": 3}


def _pontuar_opcao(opcao: dict) -> int:
    """
    Pontuação simples e explícita: menor risco e esforço somam menos,
    maior reversibilidade e evidência disponível somam mais.
    Quanto MENOR o total, melhor a opção (convém checar o cálculo no artefato).
    """
    risco = _ESCALA.get(str(opcao.get("risco", "alto")).lower(), 3)
    esforco = _ESCALA.get(str(opcao.get("esforco", "alto")).lower(), 3)
    reversibilidade = _ESCALA.get(str(opcao.get("reversibilidade", "baixa")).lower(), 1)
    tem_evidencia = 1 if opcao.get("evidencia") else 0

    # menor é melhor: risco + esforço penalizam; reversibilidade e evidência aliviam
    return (risco + esforco) - (reversibilidade + tem_evidencia)


def comparar_opcoes(id_tarefa: str, opcoes: List[Dict]) -> dict:
    """
    opcoes: lista de dicts com {nome, impacto, risco, reversibilidade, esforco, evidencia}
    Retorna a tabela comparativa + recomendação + caminho do artefato gerado.
    """
    if len(opcoes) < 2:
        raise ValueError("Comparação exige ao menos 2 opções (CONTRATO_ANALISTA_v1.md, Seção 1).")

    pontuadas = [{**op, "_pontuacao": _pontuar_opcao(op)} for op in opcoes]
    pontuadas.sort(key=lambda o: o["_pontuacao"])
    recomendada = pontuadas[0]
    sob_incerteza = not bool(recomendada.get("evidencia"))

    garantir_dir(ARTEFATOS_DIR)
    ts = timestamp()
    ts_arquivo = timestamp_arquivo()
    caminho = os.path.join(ARTEFATOS_DIR, f"ANALISE_OPCOES_{id_tarefa}_{ts_arquivo}.md")

    linhas_tabela = "\n".join(
        f"| {o['nome']} | {o.get('impacto','?')} | {o.get('risco','?')} | {o.get('reversibilidade','?')} | "
        f"{o.get('esforco','?')} | {'sim' if o.get('evidencia') else 'não'} | {o['_pontuacao']} |"
        for o in pontuadas
    )

    conteudo = f"""# Análise de Opções: {id_tarefa} (TOOL-DT-ANA-001)

**Data de Geração (UTC):** {ts}

## Tabela Comparativa
(pontuação: quanto MENOR, melhor — risco+esforço penalizam, reversibilidade+evidência aliviam)

| Opção | Impacto | Risco | Reversibilidade | Esforço | Evidência? | Pontuação |
|---|---|---|---|---|---|---|
{linhas_tabela}

## Recomendação
**{recomendada['nome']}**

{"⚠️ **Recomendação sob incerteza** — não há evidência registrada para esta opção. Tratar como hipótese, não conclusão." if sob_incerteza else "Recomendação apoiada em evidência registrada."}

## Próximo Passo
Aguardando comando humano: seguir / ajustar / descartar (TOOL-CMD-003).
"""
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)

    registrar_no_indice("ANALISE_OPCOES", caminho, extra={"id_tarefa": id_tarefa, "recomendada": recomendada["nome"], "sob_incerteza": sob_incerteza})

    return {"caminho": caminho, "recomendada": recomendada["nome"], "sob_incerteza": sob_incerteza, "tabela": pontuadas}


def gerar_teste_passa_falha(id_tarefa: str, descricao: str, criterio: str, passou: bool, evidencia: str) -> str:
    """Saída mínima alternativa do Analista: teste passa/falha com evidência."""
    garantir_dir(ARTEFATOS_DIR)
    ts = timestamp()
    ts_arquivo = timestamp_arquivo()
    caminho = os.path.join(ARTEFATOS_DIR, f"TESTE_{id_tarefa}_{ts_arquivo}.md")
    status = "PASSOU" if passou else "FALHOU"
    conteudo = f"""# Teste Passa/Falha: {id_tarefa}

**Data (UTC):** {ts}
**Descrição:** {descricao}
**Critério:** {criterio}
**Status:** {status}
**Evidência:** {evidencia}
"""
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    registrar_no_indice("TESTE", caminho, extra={"id_tarefa": id_tarefa, "status": status})
    return caminho


if __name__ == "__main__":
    print("=== Teste 1: comparação de opções ===")
    resultado = comparar_opcoes("TASK-ANA-001", [
        {"nome": "Opção A (genérica)", "impacto": "Alto", "risco": "Alto", "reversibilidade": "Baixa", "esforco": "Baixo", "evidencia": None},
        {"nome": "Opção B (restrita)", "impacto": "Médio", "risco": "Baixo", "reversibilidade": "Alta", "esforco": "Médio", "evidencia": "Padrão já testado no Orquestrador"},
        {"nome": "Opção C (adiar)", "impacto": "Baixo", "risco": "Baixo", "reversibilidade": "Alta", "esforco": "Baixo", "evidencia": None},
    ])
    print(f"Recomendada: {resultado['recomendada']} | sob incerteza: {resultado['sob_incerteza']}")
    print(f"Artefato: {resultado['caminho']}")

    print("\n=== Teste 2: teste passa/falha ===")
    caminho_teste = gerar_teste_passa_falha(
        "TASK-ANA-001", "Executor recusa token SEGUIR", "Deve levantar TokenInvalidoError",
        passou=True, evidencia="ferramenta_executor_standalone.py, Teste 1 do __main__",
    )
    print(f"Teste gerado em: {caminho_teste}")
