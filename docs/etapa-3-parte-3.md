# Etapa 3 - Parte 3

## Objetivo

Adicionar filtros e busca de leads para acelerar a operacao comercial e reduzir tempo de localizacao de oportunidades.

## Entregas

- Filtros na tela de listagem de leads:
  - busca por nome (`q`)
  - `status`
  - `nivel_interesse`
  - `evento_id`
  - `colaborador_id`
  - periodo de `data_captacao` (inicio/fim)
  - ordenacao por atualizacao, captacao e score
- URL parametrizada via `GET` para compartilhamento e integracoes futuras.
- Botao de limpar filtros.

## Arquivos alterados

- `leads/views.py`
- `templates/leads/lead_list.html`
- `static/css/main.css`

## Criterios de pronto

- Filtros aplicados corretamente em combinacao.
- Ordenacao validada contra lista permitida para evitar parametros invalidos.
- Interface pronta para evolucao em API no proximo ciclo.
