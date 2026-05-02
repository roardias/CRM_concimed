# Etapa 3 - Parte 2

## Objetivo

Habilitar registro de interacoes comerciais por lead com historico em timeline, usando a tabela `concimed_contatos`.

## Entregas

- Nova tela de detalhe de lead com:
  - resumo dos dados principais
  - formulario para novo contato
  - timeline cronologica de interacoes
- Nova rota para persistir contatos:
  - `POST /kanban/leads/<lead_id>/contatos/novo/`
- Lista de leads com acesso rapido para detalhe.

## Modelagem e integracao

- `ContatoLeadForm` criado em `leads/forms.py`.
- Persistencia realizada em `leads/views.py` com vinculo direto pelo `lead_id`.
- `colaborador_id` permanece como referencia externa para integracao com `concimed_colaboradorcomercial`.

## Fluxo operacional

1. Usuario abre lista de leads.
2. Clica em "Detalhes".
3. Registra interacao (canal, descricao, data, respondeu).
4. Sistema salva na `concimed_contatos`.
5. Timeline exibe o novo item imediatamente.
