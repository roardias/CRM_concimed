# Arquitetura do CRM Concimed

## Objetivos da Etapa 1 (concluida)

- Criar base técnica sólida e legível
- Habilitar login/senha para uso interno inicial
- Implementar Kanban inicial para tratamento de leads
- Preparar uso de banco MySQL externo como base principal

## Visão de módulos

- **core**
  - Dashboard inicial com visão resumida por eventos e leads.
- **accounts**
  - App reservado para integração futura com o sistema legado de autenticação.
- **leads**
  - `Evento`: tabela de eventos de captação (`concimed_eventos`).
  - `LeadEvento`: tabela principal de leads (`concimed_leads_eventos`).
  - `ContatoLead`: histórico de interações (`concimed_contatos`).
  - `colaborador_id` referencia `concimed_colaboradorcomercial` sem tabela local de responsáveis.

## Banco de dados (MySQL)

- O projeto usa `DB_*` para conexão MySQL.
- Configuração atual: banco remoto MySQL, com fallback SQLite para bootstrap local.
- Scripts SQL versionados em `Codigos SQL/` para evolução controlada do schema.

## Padrao oficial de nomes de tabelas

Todas as tabelas de dominio do CRM devem seguir:

- Prefixo fixo: `concimed_`
- Escrita: `snake_case`
- Minusculo e sem acentos
- Nome orientado ao dominio de negocio

Exemplos:

- `concimed_leads_eventos`
- `concimed_eventos`
- `concimed_contatos`
- `concimed_movimentacao_lead`

Implementacao no Django:

- Definir `db_table` em `class Meta` de cada model novo.

## Segurança e permissões (MVP)

- Autenticacao controlada por variavel `AUTH_ENABLED`.
- Quando `AUTH_ENABLED=False`, acesso liberado para validacao funcional.
- Quando `AUTH_ENABLED=True`, cadastros exigem login e autorizacao por perfil/grupo/permissao.
- Gestao de usuarios internos removida para evitar acoplamento com autenticacao local.
- Proxima etapa: integração SSO/usuarios do sistema principal com mapeamento de perfis.

## Convenções de código

- Organização por apps Django (separação de domínio).
- Templates reutilizando `base.html`.
- CSS e JS globais em `static/`.
- Documentação em `docs/`.

## Objetivos da Etapa 2 (concluida)

- Cadastro manual de leads (formulario)
- Listagem estruturada de leads para operacao comercial
- Filtros e busca implementados
- Estrutura preparada para integração de usuário externo

## Etapa 3 - Parte 1 (concluida)

- Projeto Django mapeado para tabelas reais do MySQL já criadas via SQL.
- Modelos em modo `managed = False` para evitar recriação de schema.
- Kanban atualizado para usar `status` de `concimed_leads_eventos`.

## Etapa 3 - Parte 2 (concluida)

- Detalhe de lead implementado com timeline de contatos.
- Registro de novo contato integrado a `concimed_contatos`.
- Lista de leads com navegacao para acompanhamento operacional.

## Etapa 3 - Parte 3 (concluida)

- Filtros e busca implementados na listagem de leads.
- URL parametrizada para facilitar compartilhamento e integracoes.
- Ordenacao comercial por atualizacao, captacao e score.

## Etapa 3 - Parte 4 (concluida)

- CRUD completo implementado para:
  - categoria profissional
  - profissao
  - especialidade
  - eventos
- Rotas dedicadas de listar, criar, editar e excluir por entidade.
- Controle de permissao aplicado com suporte a modo sem login para testes (`AUTH_ENABLED=False`).

## Etapa 3 - Parte 5 (concluida)

- Script SQL criado para nova tabela `concimed_fases_academicas`.
- Estrutura inclui:
  - `nome`
  - `tipo` (ENUM `SEMESTRE` no banco; no Django `TipoFase` inclui também `INTERNATO` e `RESIDENCIA` para evolução futura)
  - `ordem`
  - `ativo`
  - auditoria (`created_at`, `updated_at`)
- Indices e `UNIQUE` aplicados conforme padrao do banco.

## Etapa 3 - Parte 8 (concluida)

- Transições de etapa no Kanban com regras de fluxo (sem pular etapas; PERDIDO a partir de qualquer etapa exceto já perdido).
- Modal obrigatório por transição; persistência em `concimed_lead_transicoes` e criação de contato em NOVO → EM CONTATO.

## Etapa 3 - Parte 7 (concluida)

- Kanban com colunas em linha, cards compactos e movimentação por arrastar e soltar.
- Clique no card abre modal com resumo dos campos e atalho para edição do lead (`lead_update`).

## Etapa 3 - Parte 6 (concluida)

- Modelo simplificado aplicado:
  - categoria profissional
  - especialidade
  - fase academica vinculada na especialidade
- Tabela de profissoes removida do fluxo operacional.
- Regras de dependência aplicadas em backend e frontend.
- Endpoint dinamico de especialidades por categoria.
- CRUD de fases academicas integrado na area de Cadastros.

## Proxima etapa planejada (Etapa 4)

- API de integração para leads e contatos (JSON).
- Endpoints preparados para consumo do sistema principal.
