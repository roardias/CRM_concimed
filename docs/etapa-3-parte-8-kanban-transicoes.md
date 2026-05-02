# Etapa 3 - Parte 8

## Objetivo

Regras de transição no Kanban: fluxo linear (sem pular etapas), etapa PERDIDO a partir de qualquer situação exceto já perdido, e registro obrigatório dos dados de cada mudança na tabela `concimed_lead_transicoes` (e contato em NOVO → EM CONTATO).

## Validação do SQL enviado (resumo)

| Problema | Correção aplicada no `023_*.sql` |
|----------|-----------------------------------|
| FK `concimed_leads` | No projeto a tabela é **`concimed_leads_eventos`**. |
| Tipos `INT` em chaves | PK/FKs de lead e contato no schema atual são **`BIGINT`**. |
| Campos de data da regra de negócio | Incluídos **`data_contato`**, **`data_envio_proposta`**, **`data_conversao`**. |
| `BOOLEAN` em MySQL | Uso de **`TINYINT(1)`** para `respondeu` (equivalente habitual). |
| COLLATE | **`utf8mb4_unicode_ci`** alinhado ao `001`. |

## Scripts SQL

- `Codigos SQL/023_concimed_lead_transicoes.sql`

## Comportamento da aplicação

- Arrastar o card abre modal com campos conforme a transição; cancelar/fechar não move o card.
- Tentativa de pular etapa: mensagem *«Não é possível avançar para esta etapa. Conclua a etapa anterior primeiro.»* (front e back).
- Endpoint: `POST /kanban/lead/<id>/transicionar/` (FormData, `X-Requested-With: XMLHttpRequest`).

## Arquivos alterados

- `Codigos SQL/023_concimed_lead_transicoes.sql` (novo)
- `leads/kanban_transitions.py` (novo)
- `leads/models.py`
- `leads/views.py`
- `leads/urls.py`
- `templates/leads/kanban.html`
- `static/js/main.js`
- `static/css/main.css`
- `docs/etapa-3-parte-8-kanban-transicoes.md` (este arquivo)
- `docs/arquitetura.md`
- `README.md`
- `docs/cronograma.md`
