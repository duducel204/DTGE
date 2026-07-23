# Estrutura de Logs e Hashes — DTGE

## Visão Geral

O sistema centraliza toda auditoria em dois diretórios:

```
logs/
  └── DTGE_MASTER.log           # Log único, sequencial, com integridade
hashes/
  └── HASHES_REGISTRY.jsonl     # Registro de hashes de todos os artefatos
```

## Diretório `logs/`

### Arquivo: `DTGE_MASTER.log`

**Formato:** Newline-delimited JSON (JSONL), onde cada linha é um evento.

**Estrutura de entrada:**

```json
{
  "seq": 1,
  "ts": "2026-07-23T19:15:30.123456Z",
  "agente": "Orquestrador",
  "tipo": "DECIDIR",
  "mensagem": "Descrição do evento",
  "detalhes": { "chave": "valor" },
  "autorizado_por": "CEO",
  "hash": "sha256_da_entrada"
}
```

**Campos:**
- `seq` — Número sequencial único (garante ordem total mesmo com logs distribuídos)
- `ts` — Timestamp ISO 8601 com UTC
- `agente` — Nome do agente que gerou o evento
- `tipo` — Tipo de evento (ver catálogo abaixo)
- `mensagem` — Descrição textual do evento
- `detalhes` — Dados estruturados adicionais (opcional)
- `autorizado_por` — Quem autorizou (opcional, obrigatório para eventos críticos)
- `hash` — SHA-256 da entrada (sem o próprio hash)

**Tipos de eventos permitidos:**
- `DECIDIR` — Decisão estrutural
- `SEGUIR` — Avanço cognitivo (não-executivo)
- `AUTORIZACAO_EXECUCAO` — Autorização para executar
- `ALERTA` — Alerta não-crítico
- `ALERTA_INTEGRIDADE` — Violação de integridade detectada
- `HASH_REGISTRADO` — Hash de artefato registrado
- `ERRO` — Erro do sistema
- Outros conforme necessário

## Diretório `hashes/`

### Arquivo: `HASHES_REGISTRY.jsonl`

**Formato:** Newline-delimited JSON, um registro por linha.

**Estrutura de entrada:**

```json
{
  "ts": "2026-07-23T19:15:30.123456Z",
  "arquivo": "CONTRATO_ORQUESTRADOR_v1.md",
  "tipo": "contrato",
  "hash_sha256": "abc123...",
  "tamanho_bytes": 2048,
  "autorizado_por": "CEO"
}
```

**Campos:**
- `ts` — Timestamp de quando o hash foi registrado
- `arquivo` — Caminho do arquivo auditado
- `tipo` — Tipo de artefato (contrato, codigo, canonizacao, etc.)
- `hash_sha256` — Hash SHA-256 do arquivo
- `tamanho_bytes` — Tamanho do arquivo em bytes
- `autorizado_por` — Quem autorizou o registro

**Tipos de artefatos suportados:**
- `contrato` — Contrato formal do agente
- `codigo` — Código executável
- `canonizacao` — Aprovação de canonização
- `manifesto` — Manifesto de segurança (blindagem)
- `teste` — Artefato de teste
- Outros conforme necessário

## API do `dtge_logger.py`

### Funções principais:

#### `registrar_log(agente, tipo_evento, mensagem, detalhes=None, autorizado_por=None) -> dict`

Registra um evento no log centralizado.

```python
from dtge_logger import registrar_log

resultado = registrar_log(
    agente="Orquestrador",
    tipo_evento="DECIDIR",
    mensagem="Iniciando pipeline de decisão",
    detalhes={"prioridade": "alta"},
    autorizado_por="CEO"
)
# Retorna: {"seq": 1, "ts": "...", "hash": "...", "arquivo_log": "logs/DTGE_MASTER.log"}
```

#### `registrar_hash_artefato(caminho_artefato, tipo_artefato, autorizado_por) -> dict`

Registra o hash de um artefato para auditoria.

```python
from dtge_logger import registrar_hash_artefato

resultado = registrar_hash_artefato(
    caminho_artefato="CONTRATO_ORQUESTRADOR_v1.md",
    tipo_artefato="contrato",
    autorizado_por="CEO"
)
# Retorna: {"arquivo": "...", "hash_sha256": "...", "ts": "...", "registro_arquivo": "..."}
```

#### `verificar_integridade_artefato(caminho_artefato, hash_esperado) -> bool`

Verifica se um artefato não foi alterado.

```python
from dtge_logger import verificar_integridade_artefato

integro = verificar_integridade_artefato(
    caminho_artefato="CONTRATO_ORQUESTRADOR_v1.md",
    hash_esperado="abc123..."
)
```

#### `listar_logs_agente(agente, limite=50) -> list`

Retorna os últimos logs de um agente específico.

```python
from dtge_logger import listar_logs_agente

logs = listar_logs_agente(agente="Orquestrador", limite=10)
```

#### `resumo_sistema() -> dict`

Retorna estatísticas do sistema.

```python
from dtge_logger import resumo_sistema

stats = resumo_sistema()
# Retorna: {
#   "total_logs": 42,
#   "tipos_evento": {"DECIDIR": 5, "AUTORIZACAO_EXECUCAO": 3, ...},
#   "agentes_ativos": ["Orquestrador", "Sentinela", ...],
#   "total_hashes_registrados": 15,
#   ...
# }
```

## Fluxo de uso típico

### 1. Quando um agente toma uma decisão

```python
resultado = registrar_log(
    agente="Orquestrador",
    tipo_evento="DECIDIR",
    mensagem="Decisão: validar integridade do código",
    detalhes={"alvo": "ferramenta_executor_standalone.py"},
    autorizado_por="CEO"
)
```

### 2. Quando um artefato é aprovado

```python
resultado_hash = registrar_hash_artefato(
    caminho_artefato="CONTRATO_EXECUTOR_v1.md",
    tipo_artefato="contrato",
    autorizado_por="CEO"
)
```

### 3. Quando há uma violação de integridade

O sistema registra automaticamente:

```python
verificar_integridade_artefato(
    caminho_artefato="ferramenta_executor_standalone.py",
    hash_esperado="abc123..."
)
# Se não bater, gera automaticamente um ALERTA_INTEGRIDADE no log
```

## Integração com o sistema existente

Os agentes devem ser atualizados para usar `dtge_logger.py` em vez de suas próprias implementações:

**Antes (em `ferramenta_orquestrador_standalone.py`):**
```python
def registrar_no_indice(tipo_registro, ref, extra=None):
    # Implementação local
    ...
```

**Depois:**
```python
from dtge_logger import registrar_log

def registrar_evento(tipo, mensagem, detalhes):
    registrar_log(
        agente="Orquestrador",
        tipo_evento=tipo,
        mensagem=mensagem,
        detalhes=detalhes,
        autorizado_por=obter_usuario_atual()
    )
```

## Segurança e auditoria

1. **Imutabilidade:** Uma vez escrito, um log não é alterado (apenas append).
2. **Rastreabilidade:** Cada evento tem sequência, timestamp e hash.
3. **Autorização:** Eventos críticos requerem `autorizado_por` explícito.
4. **Integridade:** Hashes permitem detectar alterações em artefatos.

## Próximos passos

- [ ] Migrar todos os agentes para usar `dtge_logger.py`
- [ ] Implementar verificação automática de hashes no bootup
- [ ] Criar dashboard de visualização de logs
- [ ] Backup periódico do `DTGE_MASTER.log`
