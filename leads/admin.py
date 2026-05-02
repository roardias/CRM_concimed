from django.contrib import admin

from .models import CategoriaProfissional, ContatoLead, Especialidade, Evento, FaseAcademica, LeadEvento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "cidade", "estado", "data_evento", "data_fim")
    list_filter = ("tipo", "estado")
    search_fields = ("nome", "cidade", "local")


@admin.register(LeadEvento)
class LeadEventoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo_lead", "status", "nivel_interesse", "evento", "updated_at")
    list_filter = ("status", "nivel_interesse", "tipo_lead")
    search_fields = ("nome", "email", "telefone", "instituicao")


@admin.register(ContatoLead)
class ContatoLeadAdmin(admin.ModelAdmin):
    list_display = ("lead", "canal", "respondeu", "data_contato")
    list_filter = ("canal", "respondeu")
    search_fields = ("lead__nome", "descricao")


@admin.register(CategoriaProfissional)
class CategoriaProfissionalAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "updated_at")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria_profissional", "ativo", "updated_at")
    list_filter = ("ativo", "categoria_profissional")
    search_fields = ("nome",)


@admin.register(FaseAcademica)
class FaseAcademicaAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "ordem", "ativo", "updated_at")
    list_filter = ("tipo", "ativo")
    search_fields = ("nome",)
