# MEMORIA_DREAMTEAM_v1 — Arquivo de Contexto para Retomada

**Propósito:** este arquivo substitui precisar reexplicar tudo numa conversa nova.
Cole/reanexe ele (junto com os arquivos citados, se precisar do conteúdo
completo) no início de uma sessão nova para retomar de onde parou.

## 0) O que é este projeto
Adaptação do sistema de governança multiagente "Dream Team" (originalmente
escrito para Gemini Code Assist) para rodar neste ambiente Claude — chat +
sandbox com bash/criação de arquivo reais. Regra central herdada do
catálogo: nada existe sem registro verificável; nenhuma execução acontece
sem autorização explícita.

## 1) Estado por agente (contrato / canonizado / código / testado)

| Agente | Contrato real | Canonizado | Código real | Testado |
|---|---|---|---|---|
| Orquestrador | ✅ CONTRATO_ORQUESTRADOR_v1.md | ✅ | ✅ ferramenta_orquestrador_standalone.py | ✅ |
| Sentinela | ✅ CONTRATO_SENTINELA_v1.md | ✅ | ✅ ferramenta_sentinela_standalone.py | ✅ |
| Arquiteto | ✅ CONTRATO_ARQUITETO_v1.md | ✅ | ✅ ferramenta_arquiteto_standalone.py | ✅ |
| Analista | ✅ CONTRATO_ANALISTA_v1.md | ✅ | ✅ ferramenta_analista_standalone.py | ✅ |
| Executor | ✅ CONTRATO_EXECUTOR_v1.md | ✅ | ✅ ferramenta_executor_standalone.py | ✅ |
| Registrador | ✅ CONTRATO_REGISTRADOR_v1.md | ✅ | ✅ ferramenta_registrador_standalone.py | ✅ |
| Rollback | ✅ CONTRATO_ROLLBACK_v1.md | ✅ | ✅ ferramenta_rollback_standalone.py | ✅ |
| 01_Coletor_Continuidade | ✅ (recebido por upload) | ❌ | ❌ | ❌ |
| 02_Qualificador_Intencao | ❌ nunca existiu | ❌ | ❌ | ❌ |

Todo código compartilha `dreamteam_core.py` (helpers) e um único ledger:
`artefatos/INDICE.jsonl`.

## 2) Linha do tempo resumida (decisões-chave)
1. Catálogo (`FERRAMENTAS_v2.md`) e contrato original do Orquestrador foram lidos e entendidos.
2. Protocolo de adaptação ao ambiente Claude criado (`PROTOCOLO_DREAMTEAM_CLAUDE_v1.md`).
3. Código do Orquestrador adaptado (sem `google.adk`), depois otimizado: registro automático de uso (decorator), depois redução de tokens (JSON compacto, ledger único, template referenciado por hash em vez de repetido).
4. `BRIEFING.md` (escrito p/ Gemini) adaptado para Claude (`BRIEFING_CLAUDE_v1.md`) — só como referência, não muda comportamento automaticamente.
5. Simulação textual do time completo rodada, depois todos os 6 agentes restantes ganharam contrato simulado → aprovados pelo humano → canonizados em lote (`_BASE/CANONIZACOES/`) com 1 evento `DECIDIR` batch.
6. Executor promovido a real primeiro (Opção B: escopo restrito a bash/arquivo local); depois os outros 5 ganharam código real.
7. Auditoria técnica (TOOL-TECH-001 a 007) rodada de verdade sobre o sandbox — achou 2 bugs reais:
   - Colisão de nome de arquivo por timestamp de segundo (sobrescrita silenciosa de evidência)
   - Registrador podia reingerir o mesmo pedido duas vezes (sem idempotência)
   Ambos corrigidos e reconfirmados por teste.
8. Congelamento formal (TOOL-CMD-008): 7 contratos + 8 arquivos de código canonizados, 1 `DECIDIR` final (`CONGELAR_DREAMTEAM_v1`).
9. Recebido contrato do `01_COLETOR_CONTINUIDADE` (agente novo, upstream do Orquestrador) — ainda não construído em código.

## 3) Pendências abertas (não resolvidas)
- **02_Qualificador_Intencao**: nunca foi definido nem em contrato nem em código — é o elo que falta entre o Coletor e o Orquestrador.
- **01_Coletor_Continuidade**: contrato existe (via upload), mas sem canonização nem código.
- **Teste de integração ponta a ponta**: nunca rodamos os 7 agentes reais chamando uns aos outros em sequência — só isolados.
- **Lacunas conhecidas do Orquestrador** (achado na "revista" manual, não normativo): código não captura `criticidade`, não checa repetição de `(agente_destino, parametros)`, não faz consulta anti-drift, não implementa "Análise de Opções"/Pausa.

## 4) Como retomar
- Se estiver num Project com estes arquivos already anexados: só peça para eu reler o arquivo relevante.
- Se for uma conversa nova sem Project: reanexe pelo menos este arquivo de memória; anexe os `.py`/`.md` específicos só se for mexer neles de fato (economiza tokens não subir tudo de uma vez).
- Ordem sugerida do próximo passo: (a) construir 02_Qualificador_Intencao, (b) codificar 01_Coletor_Continuidade, (c) rodar integração ponta a ponta, (d) fechar as lacunas do Orquestrador.

## 5) Inventário de arquivos (34 artefatos gerados até aqui)
- Contratos reais: 7 × `CONTRATO_<AGENTE>_v1.md`
- Código: `dreamteam_core.py` + 7 × `ferramenta_<agente>_standalone.py`
- Canonizações: 15 arquivos em `_BASE/CANONIZACOES/` (7 contratos + 8 códigos)
- Protocolo/Briefing: `PROTOCOLO_DREAMTEAM_CLAUDE_v1.md`, `BRIEFING_CLAUDE_v1.md`
- Scripts de processo: `canonizar_dreamteam.py`, `congelar_dreamteam_v1.py`
- Eventos-chave: `DECIDIR_CONGELAMENTO_v1.json` (congelamento final)
- Simulações (não reais, mantidas só como histórico): pasta `simulacao_dreamteam/` (contratos simulados que foram promovidos, eventos simulados de exemplo)
