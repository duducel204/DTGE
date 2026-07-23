PLANO_MIGRACAO_GITHUB_v1 — Reorganização de Repositório
Regra de ouro deste plano: nenhum artefato já canonizado é sobrescrito ou
apagado. Mover de lugar é tratado como um evento de governança formal — a
mesma lógica do Rollback ("nunca sobrescreve, sempre encadeia") se aplica aqui.

0) Pré-requisito de governança (BC-001)
_BASE/CANONIZACOES/ é citado literalmente no catálogo (TOOL-CMD-008) como
onde a canonização "só existe". Renomear/mover esse caminho é uma mudança de
nível BC-001, não um refactor cosmético. Por isso, o passo 1 abaixo é
obrigatório antes de qualquer git mv.

1) Autorização formal (DECIDIR) — fazer ANTES de mexer em qualquer arquivo
Gere e assine (você, humano) um evento DECIDIR explícito autorizando a
migração, referenciando o mapeamento completo de caminhos antigo→novo. O
script migrar_para_github_v1.py (anexo) faz isso por você na Etapa A.

2) Preparar o novo layout (sem mexer no antigo ainda)
Código

3) Rodar a Etapa A do script (preparação, 100% local, sem git ainda)
Código

Isso:
Confere a integridade de TUDO que já existe (contratos, código, cadeia do
Registrador, chain de tokens) ANTES de mover — se algo já estiver
quebrado, o script para aqui e avisa, sem tocar em nada.
Gera o mapeamento completo MAPEAMENTO_MIGRACAO_v1.json (caminho antigo →
caminho novo) para cada arquivo.
Gera uma nova canonização por artefato em _BASE/CANONIZACOES/, do
tipo "SUCESSAO" — referenciando a canonização ORIGINAL (nunca apagada) +
o caminho novo + o hash do conteúdo (que não muda, só o local muda).
Gera o evento DECIDIR formal autorizando a migração (Passo 1).
Idempotente: rodar --preparar de novo não duplica nada — se o
mapeamento e as sucessões já existem, o script detecta e pula.

4) Só agora, mover de fato (comandos reais)
Bash

O script gera comandos git mv (preserva histórico de commit no Git — mv
puro não preserva; git mv sim). Exemplo do que sai gerado:
Bash

5) Corrigir imports — NÃO usar shim raso (import main)
Achado real do nosso código: módulos importam nomes específicos, não só
rodam main() (ex.: from ferramenta_orquestrador_standalone import gerar_evento, gerar_hash_sha256). Um shim que só chama main() quebra isso.
Shim correto (re-exporta os nomes, não só executa):
Python

Repetir esse padrão pra cada um dos 8 shims (core, orquestrador, executor,
sentinela, arquiteto, analista, registrador, rollback, token_autorizacao).

6) Centralizar paths (config.py) — SEM alterar comportamento de arquivos já existentes
Python

Atualizar os módulos pra importar PATHS em vez de strings soltas — mas só
DEPOIS que a Etapa A já re-canonizovou tudo (Passo 3), pra não misturar as
duas mudanças no mesmo commit.

7) Verificação pós-migração (obrigatória antes de merge)
Código

Confirma: (a) todo arquivo do mapeamento existe no caminho novo, (b) hash de
conteúdo bate com o registrado na sucessão, (c) cadeia de tokens/registrador
ainda resolve sem erro usando os caminhos novos.

8) .gitignore
Código

NÃO ignorar /contracts/, /canonizations/ — são a fonte auditável.

9) Commit, PR, merge
Bash

10) Rollback do próprio processo de migração (se algo der errado)
Como nada foi sobrescrito (Passo 3 só ADICIONA sucessões, não apaga
originais), reverter é: git checkout main -- . na branch, ou simplesmente
não dar merge no PR. As canonizações antigas continuam válidas e íntegras.
