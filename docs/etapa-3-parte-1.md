# Etapa 3 - Parte 1

## Objetivo

Conectar a aplicacao Django ao schema MySQL definitivo criado manualmente, sem gerar novas tabelas via ORM.

## Decisoes tecnicas

- Modelos do app `leads` mapeados para:
  - `concimed_eventos`
  - `concimed_leads_eventos`
  - `concimed_contatos`
- Todos estes modelos usam `managed = False`.
- `colaborador_id` permanece como ID externo para integracao com `concimed_colaboradorcomercial`.

## Ajustes de interface

- Kanban agora usa os status do lead:
  - `novo`
  - `em_contato`
  - `proposta_enviada`
  - `convertido`
  - `perdido`
- Tela de listagem de leads atualizada para os novos campos de dominio.
- Formulario de lead atualizado para capturar os campos do schema atual.

## Impacto para proxima etapa

- Base pronta para implementar filtros e busca sem retrabalho de estrutura.
- Base pronta para adicionar historico de contatos por lead.
