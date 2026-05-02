# Etapa 3 - Parte 6

## Objetivo

Aplicar o novo modelo simplificado:

- Categoria profissional -> Especialidade
- Fase acadêmica vinculada na especialidade (quando aplicável)

## Entregas

- `LeadForm` atualizado com campos:
  - `categoria_profissional` (obrigatório)
  - `especialidade` (obrigatório)
- Validações backend implementadas para bloquear inconsistências:
  - especialidade fora da categoria
  - estudante com especialidade sem fase acadêmica vinculada
- Fase de internato como dado derivado:
  - propriedade `internato_implicito` em `LeadEvento`
- APIs de dependência para frontend:
  - `/kanban/api/especialidades/?categoria_id=...`
- Formulário de lead com comportamento dinâmico:
  - carrega especialidades por categoria
  - limpa seleção ao alterar categoria
- CRUD de `fases_academicas` adicionado em Cadastros.

## Scripts SQL relacionados

- `Codigos SQL/005a_antes_drop_fk_profissao.sql` / `005a_antes_drop_coluna_profissao.sql` — opcionais se ainda existir `profissao_id` (erro 1091 = já aplicado).
- `Codigos SQL/005a_migracao_especialidade.sql` — vincula especialidade à categoria (índice, UK, FK). Fase acadêmica fica só no lead e na tabela `concimed_fases_academicas`.
- `Codigos SQL/005b_seed_categorias.sql` — insere categorias (um arquivo, um comando; evita erro 1064 no DBeaver com varios INSERT no mesmo script).
- `Codigos SQL/005c_seed_especialidades.sql` — insere especialidades. Rodar depois do 005b.
