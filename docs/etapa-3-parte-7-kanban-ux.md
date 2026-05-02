# Etapa 3 - Parte 7

## Objetivo

Melhorar a página Kanban de tratamento de leads: colunas em linha com cards compactos, resumo do lead em modal ao clicar (com edição, sem exclusão) e movimentação por arrastar e soltar entre etapas.

## Entregas

- Layout horizontal com scroll (`flex` + colunas estreitas), tipografia e cards reduzidos.
- Clique no card abre `<dialog>` com HTML carregado de `GET /kanban/leads/<id>/preview/`; ações «Editar lead» e «Fechar» (sem opção de excluir).
- Nova rota e view `lead_update` em `/kanban/leads/<id>/editar/` reutilizando `LeadForm` e o template de cadastro.
- Drag-and-drop entre colunas com `POST` AJAX em `move_lead`; resposta JSON quando `X-Requested-With: XMLHttpRequest`.
- Remoção do seletor «Mover para» dos cards (substituído pelo arraste).

## Scripts SQL relacionados

- Nenhum (alterações apenas em aplicação Django, templates, CSS e JS).

## Arquivos alterados

- `leads/views.py`
- `leads/urls.py`
- `templates/leads/kanban.html`
- `templates/leads/kanban_lead_preview.html` (novo)
- `templates/leads/lead_create.html`
- `static/css/main.css`
- `static/js/main.js`
- `docs/etapa-3-parte-7-kanban-ux.md` (este arquivo)
- `docs/arquitetura.md`
