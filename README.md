# CRM Concimed

Projeto inicial do CRM da Concimed, construído para evoluir por etapas com arquitetura profissional, documentação clara e foco em integrações futuras.

## Stack atual

- **Backend:** Python + Django
- **Frontend:** HTML + CSS + JavaScript
- **Banco:** MySQL externo (com fallback local SQLite para desenvolvimento inicial)
- **Auth:** login/senha inicial via Django Auth (temporário até integrar com o sistema principal)

## Como rodar

1. Criar ambiente virtual:
   - Windows PowerShell: `python -m venv .venv`
2. Instalar dependências:
   - `.\.venv\Scripts\python -m pip install -r requirements.txt`
3. Configurar variáveis:
   - Copiar `.env.example` para `.env` e preencher credenciais do MySQL.
   - Definir `AUTH_ENABLED=False` para ambiente de teste sem login.
   - Definir `AUTH_ENABLED=True` para exigir login e permissao nas areas restritas.
4. Migrar banco:
   - `.\.venv\Scripts\python manage.py makemigrations`
   - `.\.venv\Scripts\python manage.py migrate`
5. Criar superusuário:
   - `.\.venv\Scripts\python manage.py createsuperuser`
6. Iniciar aplicação:
   - `.\.venv\Scripts\python manage.py runserver`

## Estrutura inicial

- `concimed_crm/`: configuração principal do projeto Django
- `core/`: dashboard inicial
- `accounts/`: app reservada para integração futura de autenticação
- `leads/`: Kanban e pipeline de leads
- `templates/`: templates HTML
- `static/`: arquivos de estilo e JavaScript
- `docs/`: documentação funcional e técnica

## Schema atual integrado

- `concimed_eventos`
- `concimed_leads_eventos`
- `concimed_contatos`
- `concimed_fases_academicas`
- Referência externa: `concimed_colaboradorcomercial`

## Scripts SQL versionados

- `Codigos SQL/001_criacao_tabelas_crm_concimed.sql`
- `Codigos SQL/002_tabelas_classificacao_profissional.sql`
- `Codigos SQL/003_tabela_fases_academicas.sql`
- `Codigos SQL/004_alter_leads_hierarquia_academica.sql`
- `Codigos SQL/005a_antes_drop_fk_profissao.sql` (opcional: ignore 1091 se a FK ja nao existir)
- `Codigos SQL/005a_antes_drop_coluna_profissao.sql` (opcional: ignore 1091 se a coluna ja nao existir)
- `Codigos SQL/005a_migracao_especialidade.sql` (categoria + indice + UK + FK na especialidade)
- `Codigos SQL/005b0_listar_categorias_existentes.sql` (opcional, consulta)
- `Codigos SQL/005b_seed_categorias.sql` (seed categorias, INSERT IGNORE, nao duplica por nome)
- `Codigos SQL/005c_seed_especialidades.sql` (seed especialidades, depois do 005b)
- `Codigos SQL/005d_seed_categorias_estudantes.sql` (Estudante de Medicina + Estudante da Área da Saúde)
- `Codigos SQL/009_pre_add_fase_academica_id_leads.sql` (se `concimed_leads_eventos` ainda não tiver `fase_academica_id`; necessário antes do 009a)
- `Codigos SQL/009a_leads_null_fase_internato_residencia.sql` + `009b_delete_fases_internato_residencia.sql` + `009c_alter_fases_tipo_somente_ano.sql` (migração fases só ANO; rode nessa ordem, um arquivo por vez no DBeaver se der 1064 em lote)
- `Codigos SQL/009_migracao_fases_academicas_somente_ano.sql` (mesmo conteúdo dos três acima em um único arquivo; use os 009a–009c se o cliente não aceitar vários comandos juntos)
- `Codigos SQL/010_seed_fases_academicas_anos.sql` (1º ao 12º semestre + Não informado, tipo SEMESTRE; ambientes novos)
- `Codigos SQL/024_migracao_fases_anos_para_semestres.sql` (bases com 1º–6º ano: troca catálogo para 12 semestres e realoca `fase_academica_id` nos leads conforme mapeamento ano→semestre)
- `Codigos SQL/025_alter_fases_tipo_semestre.sql` (após o 024: ENUM `tipo` de `ANO` para `SEMESTRE`; rode os 3 comandos na ordem, um por vez se necessário)
- `Codigos SQL/011_add_leads_categoria_profissional_id.sql` + `012_add_leads_profissao_id.sql` + `013_add_leads_especialidade_id.sql` (um arquivo por execução no DBeaver; complementa o `009_pre`)
- `Codigos SQL/014_concimed_estado.sql` depois `014b_concimed_cidade.sql` — tabelas `concimed_estado` e `concimed_cidade` (nesta ordem; evita erro 1824)
- `Codigos SQL/016_seed_concimed_estados.sql` — UFs (IBGE)
- `Codigos SQL/017_cidades_part_01.sql` … `017_cidades_part_14.sql` — municípios (um arquivo por execução; gerar: `python scripts/gerar_seed_concimed_cidades.py`; fonte: [Estados-Cidades-IBGE](https://github.com/chandez/Estados-Cidades-IBGE))
- `Codigos SQL/018_leads_telefone_somente_digitos.sql` — opcional (MySQL 8+): limpa máscara em `telefone` já gravado
- `Codigos SQL/019a` + `019b` + `019c` — `colaborador_id` NULL em leads (cadastro sem comercial; rode na ordem, um por vez)
- `Codigos SQL/015a` … `015l` — colunas e FKs `estado_id` / `cidade_id` em `concimed_leads_eventos` e `concimed_eventos` (um `.sql` por execução)
- `Codigos SQL/011b_leads_hierarquia_indices_e_fks.sql` (opcional: índices + FKs nos mesmos campos)
- `Codigos SQL/008_drop_fase_academica_da_especialidade.sql` (remove fase da tabela especialidade: fase fica so em leads + cadastro de fases)
- `Codigos SQL/007_alter_uk_especialidade_categoria_nome.sql` (um ALTER: remove UK antigo e cria UK categoria+nome)
- `Codigos SQL/007_add_unique_categoria_nome_somente.sql` (só ADD UNIQUE, se o 007 falhar porque o índice antigo já não existe)
- `Codigos SQL/023_concimed_lead_transicoes.sql` — histórico de transições de etapa do Kanban (`concimed_lead_transicoes`; FKs para `concimed_leads_eventos`, `concimed_colaboradorcomercial`, `concimed_contatos`)
- `Codigos SQL/026_delete_leads_eventos_duplicados_lote.sql` — exclusão pontual de leads duplicados (transições + contatos + lead); editar IDs se precisar de outro lote

## Documentacao por etapas

- `docs/cronograma.md`
- `docs/arquitetura.md`
- `docs/etapa-3-parte-1.md`
- `docs/etapa-3-parte-2.md`
- `docs/etapa-3-parte-3.md`
- `docs/etapa-3-parte-4.md`
- `docs/etapa-3-parte-6-hierarquia-leads.md`
- `docs/etapa-3-parte-7-kanban-ux.md`
- `docs/etapa-3-parte-8-kanban-transicoes.md`

## Padrao de nomes de tabelas

Todas as tabelas de dominio devem usar prefixo `concimed_` com `snake_case`.
No Django, isso e aplicado com `db_table` em `class Meta` de cada model.

## Papeis de usuario (MVP)

- Nesta fase, a gestão de usuários locais foi removida para evitar acoplamento.
- O Kanban usa `colaborador_id` como referencia externa, pronto para integracao com sistema principal.

## Proximas etapas sugeridas

1. Drag-and-drop no Kanban
2. API de integracao com sistema principal
3. Reativar autenticacao com perfis e permissao granular
4. Integracoes (WhatsApp, e-mail, agenda, ERPs)
5. Relatorios e indicadores comerciais
