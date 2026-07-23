# -*- coding: utf-8 -*-
"""
CONTRATO_QUALIFICADOR_INTENCAO_v1.md — Agente 02_QUALIFICADOR_INTENCAO

Responsável por receber intenções brutas (do Coletor) e qualificá-las:
- Valida estrutura
- Adiciona contexto de continuidade
- Determina criticidade
- Passa para Orquestrador
"""

contrato_qualificador = """
# CONTRATO_v1 — Agente 02_QUALIFICADOR_INTENCAO

**ID do Artefato:** `CONTRATO-QUAL-001`
**Status:** CANDIDATO (aguardando aprovação formal)

## 1. Objetivo

O Qualificador Intenção recebe intenções brutas (ex: "deploy app") e as transforma em Intenções Qualificadas estruturadas, prontas para o Orquestrador processar.

### Transformação realizada:

```
Intenção Bruta (texto)
    ↓
[Qualificador]
    ↓
Intenção Qualificada (JSON estruturado)
    ↓
Orquestrador
```

## 2. Entradas e Saídas

### Entradas
- **Obrigatória:** Intenção Bruta (dict ou texto):
  - `texto_bruto`: String descrevendo a ação desejada
  - `contexto_continuidade`: Dict opcional com histórico
  - `usuario_origem`: String (quem solicitou)
  - `timestamp_requisicao`: ISO 8601

### Saídas
- **Principal:** Intenção Qualificada (JSON estruturado):
  ```json
  {
    "id_intencao": "INT-DEPLOY-APP-STAGING-20260723T192737Z",
    "tipo": "EXECUCAO" | "ANALISE" | "ARQUITETURA",
    "criticidade": "BAIXA" | "MEDIA" | "ALTA" | "CRITICA",
    "parametros": { ... },
    "contexto_continuidade": { ... },
    "usuario_origem": "...",
    "timestamp_criacao": "..."
  }
  ```
- **Alternativa:** Pedido de esclarecimento (se intenção for ambígua)
- **Alternativa 2:** Rejeição (se violação de regra de negócio)

## 3. Regras de Negócio (Invariantes)

### Regra Dura 1: Estrutura Obrigatória
Nenhuma Intenção Qualificada é gerada sem os 7 campos acima preenchidos.

### Regra Dura 2: Mapeamento de Criticidade
- Contém "rollback", "reverter", "desativar" → CRITICA
- Contém "deploy", "produção", "ativar" → ALTA
- Contém "teste", "sandbox", "staging" → MEDIA
- Análise, consulta, validação → BAIXA

### Regra Dura 3: Continuidade
Se contexto_continuidade foi fornecido:
  - Registrar profundidade_ciclo do contexto anterior
  - Bloquear se profundidade > 3 (anti-loop infinito)

### Regra de Negócio 1: Deduplicação
Se a mesma intenção (mesmo texto_bruto + contexto) foi processada nos últimos 60s,
retornar a ID anterior em vez de criar duplicata.

## 4. Falhas Esperadas & Tratamento

| Cenário | Tratamento |
|---------|------------|
| Texto vago (ex: "fazer algo") | Pedir esclarecimento |
| Tipo não reconhecido | Sugerir tipos válidos |
| Loop infinito detectado | Blocar + ALERTA |
| Usuário não identificado | Rejeitar (requer autenticação) |

## 5. Dependências
- Nenhuma (primeiro agente real na cadeia, depois do Coletor)
- Precisa existir: Orquestrador (para receber saídas)

## 6. Pendências
- [ ] Integração com sistema de autenticação de usuários (não existe ainda)
- [ ] Cache de deduplicação (armazenar últimas 100 intenções em 60s)

"""

print(contrato_qualificador)
