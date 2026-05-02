from django.urls import path

from . import views

urlpatterns = [
    path("api/estados/", views.api_estados, name="api-estados"),
    path("api/cidades/", views.api_cidades, name="api-cidades"),
    path("api/especialidades/", views.api_especialidades_por_categoria, name="api-especialidades-por-categoria"),
    path("cadastros/", views.catalogos, name="catalogos"),
    path("cadastros/categorias/", views.categoria_profissional_crud, name="catalog-categoria"),
    path("cadastros/categorias/<int:pk>/editar/", views.categoria_profissional_update, name="catalog-categoria-edit"),
    path("cadastros/categorias/<int:pk>/excluir/", views.categoria_profissional_delete, name="catalog-categoria-delete"),
    path("cadastros/especialidades/", views.especialidade_crud, name="catalog-especialidade"),
    path("cadastros/especialidades/<int:pk>/editar/", views.especialidade_update, name="catalog-especialidade-edit"),
    path("cadastros/especialidades/<int:pk>/excluir/", views.especialidade_delete, name="catalog-especialidade-delete"),
    path("cadastros/eventos/", views.evento_crud, name="catalog-evento"),
    path("cadastros/eventos/<int:pk>/editar/", views.evento_update, name="catalog-evento-edit"),
    path("cadastros/eventos/<int:pk>/excluir/", views.evento_delete, name="catalog-evento-delete"),
    path("cadastros/fases-academicas/", views.fase_academica_crud, name="catalog-fase-academica"),
    path("cadastros/fases-academicas/<int:pk>/editar/", views.fase_academica_update, name="catalog-fase-academica-edit"),
    path("cadastros/fases-academicas/<int:pk>/excluir/", views.fase_academica_delete, name="catalog-fase-academica-delete"),
    path("leads/", views.lead_list, name="lead-list"),
    path("leads/novo/", views.lead_create, name="lead-create"),
    path("leads/<int:lead_id>/preview/", views.kanban_lead_preview, name="kanban-lead-preview"),
    path("leads/<int:lead_id>/editar/", views.lead_update, name="lead-update"),
    path("leads/<int:lead_id>/", views.lead_detail, name="lead-detail"),
    path("leads/<int:lead_id>/contatos/novo/", views.contato_create, name="contato-create"),
    path("", views.kanban_board, name="kanban-board"),
    path("lead/<int:lead_id>/transicionar/", views.move_lead_transition, name="move-lead-transition"),
]
