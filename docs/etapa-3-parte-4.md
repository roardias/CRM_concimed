# Etapa 3 - Parte 4

## Objetivo

Criar CRUD completo para dados base do funil e classificacao profissional.

## Entregas

- Area de cadastros com CRUD completo por entidade:
  - `categoria_profissional`
  - `profissao`
  - `especialidade`
  - `eventos`
- Operacoes disponiveis em cada entidade:
  - listar
  - criar
  - editar
  - excluir
- Dashboard de cadastros com totais e links de acesso rapido.
- Rotulos de navegacao ajustados para linguagem de usuario ("Gerenciar ...").
- Campo `ativo` removido da criacao de categoria/profissao/especialidade (entra ativo por padrao).
- Opcao de ativar/inativar mantida na edicao.

## Permissao

- Controle feito por `AUTH_ENABLED`:
  - `AUTH_ENABLED=False`: acesso liberado para ambiente de teste sem login.
  - `AUTH_ENABLED=True`: exige autenticacao e aplica regras de autorizacao.
- Regras quando `AUTH_ENABLED=True`:
  - `is_superuser`
  - `is_staff`
  - usuarios do grupo `cadastros` ou `crm_cadastros`
  - usuarios com permissao de cadastro/edicao no app `leads`
- Excluir registros:
  - permitido somente para administrador (`superuser`).

## Rotas principais do CRUD

- Home dos cadastros: `kanban/cadastros/`
- Categoria: `kanban/cadastros/categorias/`
- Profissao: `kanban/cadastros/profissoes/`
- Especialidade: `kanban/cadastros/especialidades/`
- Evento: `kanban/cadastros/eventos/`

## Arquivos alterados

- `leads/models.py`
- `leads/forms.py`
- `leads/views.py`
- `leads/urls.py`
- `templates/leads/catalogos_home.html`
- `templates/leads/catalog_categoria.html`
- `templates/leads/catalog_profissao.html`
- `templates/leads/catalog_especialidade.html`
- `templates/leads/catalog_evento.html`
- `templates/leads/catalog_edit.html`
- `templates/base.html`
- `static/css/main.css`
