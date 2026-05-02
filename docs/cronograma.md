# Cronograma de Implementacao

## Status geral

- **Etapa 1 - Base do projeto:** concluida
- **Etapa 2 - Operacao comercial inicial:** concluida
- **Etapa 3 - Integracao com schema real + produtividade:** concluida
- **Etapa 4 - API de integracao:** planejada

## Detalhamento por etapa

### Etapa 1 (concluida)

- Estrutura Django modular (`core`, `accounts`, `leads`).
- Conexao em MySQL via `.env`.
- Login basico para uso interno temporario.
- Design inicial e layout navegavel.

### Etapa 2 (concluida)

- Cadastro e listagem de leads.
- Kanban operacional.
- Padrao oficial de nomes de tabelas com prefixo `concimed_`.
- Remocao de tabela local de responsaveis para evitar acoplamento.

### Etapa 3 (concluida)

- Parte 1: mapeamento para tabelas reais (`managed = False`).
- Parte 2: detalhe do lead + registro de contatos + timeline.
- Parte 3: filtros e busca avancada na lista de leads.
- Parte 4: CRUD completo de cadastros base (categoria, profissao, especialidade, evento).
- Permissoes de cadastros com modo configuravel por `AUTH_ENABLED`.
- Parte 5: script da tabela `concimed_fases_academicas` seguindo padrao SQL do projeto.
- Parte 6: simplificacao para categoria/especialidade/fase e retirada de profissoes do fluxo.
- Parte 7: Kanban horizontal, modal de resumo do lead, edição pelo Kanban, drag-and-drop entre etapas.
- Parte 8: regras de transição de etapas, modal com dados obrigatórios, tabela `concimed_lead_transicoes`.

### Etapa 4 (proxima)

- API REST (JSON) para:
  - listar/criar/atualizar leads
  - listar/criar contatos
  - consulta de eventos
- Tokens de integracao e contratos de payload documentados.

## Documentos relacionados

- `docs/arquitetura.md`
- `docs/etapa-3-parte-1.md`
- `docs/etapa-3-parte-2.md`
- `docs/etapa-3-parte-3.md`
- `docs/etapa-3-parte-4.md`
- `docs/etapa-3-parte-6-hierarquia-leads.md`
- `docs/etapa-3-parte-7-kanban-ux.md`
- `docs/etapa-3-parte-8-kanban-transicoes.md`
