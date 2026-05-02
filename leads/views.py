from datetime import datetime

from django.contrib import messages
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Case, IntegerField, Value, When
from django.http import JsonResponse
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.views.decorators.http import require_POST

from .forms import (
    CategoriaProfissionalCreateForm,
    CategoriaProfissionalEditForm,
    ContatoLeadForm,
    EspecialidadeCreateForm,
    EspecialidadeEditForm,
    EventoForm,
    FaseAcademicaCreateForm,
    FaseAcademicaEditForm,
    LeadForm,
)
from .kanban_transitions import transition_allowed
from .models import (
    CategoriaProfissional,
    Cidade,
    ContatoLead,
    Especialidade,
    Estado,
    Evento,
    FaseAcademica,
    LeadEvento,
    LeadTransicao,
)


def _ensure_catalog_permission(request):
    if not settings.AUTH_ENABLED:
        return
    if not request.user.is_authenticated:
        raise PermissionDenied("Login necessario para acessar cadastros.")
    has_group_access = request.user.groups.filter(name__in=["cadastros", "crm_cadastros"]).exists()
    has_perm_access = request.user.has_perm("leads.add_evento") or request.user.has_perm("leads.change_evento")
    if not (request.user.is_superuser or request.user.is_staff or has_group_access or has_perm_access):
        raise PermissionDenied("Sem permissao para gerenciar cadastros.")


def _with_outros_last(queryset):
    return queryset.annotate(
        outros_last=Case(
            When(nome__iexact="Outros", then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by("outros_last", "nome")


def _can_delete_catalog(request):
    return settings.AUTH_ENABLED and request.user.is_authenticated and request.user.is_superuser


def _ensure_delete_permission(request):
    if not _can_delete_catalog(request):
        raise PermissionDenied("Somente administrador pode excluir registros.")


def _is_duplicate_key_integrity_error(exc: IntegrityError) -> bool:
    """Detecta erro 1062 (duplicate key) do MySQL / texto 'Duplicate entry'."""
    args = getattr(exc, "args", ()) or ()
    if args and args[0] == 1062:
        return True
    cause = getattr(exc, "__cause__", None)
    if cause is not None:
        cargs = getattr(cause, "args", ()) or ()
        if cargs and cargs[0] == 1062:
            return True
    return "duplicate" in str(exc).lower()


def _save_form_commit_with_integrity_handling(
    request,
    form,
    *,
    duplicate_message: str,
    other_integrity_message: str | None = None,
) -> bool:
    """
    Chame após form.is_valid(). Retorna True se o registro foi salvo.
    Em violação de unicidade, exibe mensagem amigável e reexibe o formulário.
    """
    other = other_integrity_message or (
        "Não foi possível salvar. Verifique os dados ou vínculos obrigatórios."
    )
    try:
        form.save()
    except IntegrityError as e:
        msg = duplicate_message if _is_duplicate_key_integrity_error(e) else other
        messages.error(request, msg)
        form.add_error(None, msg)
        return False
    return True


def _parse_datetime_local(value: str):
    s = (value or "").strip()
    if not s:
        return None
    dt = parse_datetime(s)
    if dt is None:
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _parse_date_required(value: str):
    s = (value or "").strip()
    if not s:
        return None
    return parse_date(s)


def _parse_id_list(values):
    out = []
    for raw in values:
        s = (raw or "").strip()
        if not s:
            continue
        try:
            out.append(int(s))
        except ValueError:
            continue
    return out


def kanban_board(request):
    status_columns = [
        ("novo", "Novo"),
        ("em_contato", "Em Contato"),
        ("proposta_enviada", "Proposta Enviada"),
        ("convertido", "Convertido"),
        ("perdido", "Perdido"),
    ]
    q = request.GET.get("q", "").strip()
    data_capt_inicio = request.GET.get("data_capt_inicio", "").strip()
    data_capt_fim = request.GET.get("data_capt_fim", "").strip()
    evento_ids = _parse_id_list(request.GET.getlist("evento_id"))
    categoria_ids = _parse_id_list(request.GET.getlist("categoria_profissional_id"))
    especialidade_ids = _parse_id_list(request.GET.getlist("especialidade_id"))

    leads = LeadEvento.objects.select_related(
        "evento",
        "categoria_profissional",
        "especialidade",
    ).all()

    if q:
        leads = leads.filter(nome__icontains=q)
    if data_capt_inicio:
        leads = leads.filter(data_captacao__gte=data_capt_inicio)
    if data_capt_fim:
        leads = leads.filter(data_captacao__lte=data_capt_fim)
    if evento_ids:
        leads = leads.filter(evento_id__in=evento_ids)
    if categoria_ids:
        leads = leads.filter(categoria_profissional_id__in=categoria_ids)
    if especialidade_ids:
        leads = leads.filter(especialidade_id__in=especialidade_ids)

    leads = leads.order_by("-updated_at", "-id")

    leads_list = list(leads)
    total_leads_filtrados = len(leads_list)

    filtros_ativos_count = sum(
        [
            bool(q),
            bool(data_capt_inicio),
            bool(data_capt_fim),
            bool(evento_ids),
            bool(categoria_ids),
            bool(especialidade_ids),
        ]
    )

    kanban_data = []
    for status_value, status_label in status_columns:
        kanban_data.append(
            {
                "value": status_value,
                "label": status_label,
                "leads": [lead for lead in leads_list if lead.status == status_value],
            }
        )

    eventos_opts = Evento.objects.all().order_by("-data_evento", "nome")
    categorias_opts = _with_outros_last(CategoriaProfissional.objects.filter(ativo=True))
    especialidades_opts = _with_outros_last(
        Especialidade.objects.filter(ativo=True).select_related("categoria_profissional")
    )

    return render(
        request,
        "leads/kanban.html",
        {
            "kanban_data": kanban_data,
            "status_columns": status_columns,
            "eventos_opts": eventos_opts,
            "categorias_opts": categorias_opts,
            "especialidades_opts": especialidades_opts,
            "total_leads_filtrados": total_leads_filtrados,
            "filtros_ativos_count": filtros_ativos_count,
            "filtros": {
                "q": q,
                "data_capt_inicio": data_capt_inicio,
                "data_capt_fim": data_capt_fim,
                "evento_ids": evento_ids,
                "categoria_ids": categoria_ids,
                "especialidade_ids": especialidade_ids,
            },
        },
    )


def kanban_lead_preview(request, lead_id):
    lead = get_object_or_404(
        LeadEvento.objects.select_related(
            "evento",
            "categoria_profissional",
            "especialidade",
            "fase_academica",
            "estado_local",
            "cidade_local",
        ),
        pk=lead_id,
    )
    return render(request, "leads/kanban_lead_preview.html", {"lead": lead})


@require_POST
def move_lead_transition(request, lead_id):
    """
    Move o lead no Kanban com registro obrigatório em concimed_lead_transicoes
    (e contato quando NOVO → EM CONTATO). Somente AJAX (FormData + CSRF).
    """
    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return HttpResponseBadRequest("Requer X-Requested-With: XMLHttpRequest")

    valid_status = {"novo", "em_contato", "proposta_enviada", "convertido", "perdido"}
    new_status = (request.POST.get("etapa_nova") or request.POST.get("status") or "").strip()
    if new_status not in valid_status:
        return JsonResponse({"ok": False, "error": "validation", "message": "Etapa inválida."}, status=400)

    lead = get_object_or_404(LeadEvento, pk=lead_id)
    old_status = lead.status
    posted_old = (request.POST.get("etapa_anterior") or "").strip()
    if posted_old and posted_old != old_status:
        return JsonResponse(
            {
                "ok": False,
                "error": "stale",
                "message": "O lead foi alterado. Recarregue o Kanban e tente de novo.",
            },
            status=409,
        )

    allowed, rule_msg = transition_allowed(old_status, new_status)
    if not allowed:
        return JsonResponse({"ok": False, "error": "rule", "message": rule_msg or "Transição não permitida."}, status=400)

    colaborador_raw = (request.POST.get("colaborador_id") or "").strip()
    if not colaborador_raw:
        return JsonResponse({"ok": False, "error": "validation", "message": "Informe o colaborador (ID)."}, status=400)
    try:
        colaborador_id = int(colaborador_raw)
    except ValueError:
        return JsonResponse({"ok": False, "error": "validation", "message": "Colaborador inválido."}, status=400)

    canal_values = {c.value for c in LeadTransicao.CanalTransicao}
    motivo_values = {c.value for c in LeadTransicao.MotivoPerda}

    try:
        with transaction.atomic():
            contato_ref = None
            t_kwargs = {
                "lead": lead,
                "colaborador_id": colaborador_id,
                "etapa_anterior": old_status,
                "etapa_nova": new_status,
            }

            if new_status == "perdido":
                motivo = (request.POST.get("motivo_perda") or "").strip()
                observacao = (request.POST.get("observacao") or "").strip()
                if motivo not in motivo_values:
                    return JsonResponse(
                        {"ok": False, "error": "validation", "message": "Selecione o motivo da perda."},
                        status=400,
                    )
                if not observacao:
                    return JsonResponse(
                        {"ok": False, "error": "validation", "message": "Observação é obrigatória."},
                        status=400,
                    )
                t_kwargs.update(
                    motivo_perda=motivo,
                    observacao=observacao,
                )
                LeadTransicao.objects.create(**t_kwargs)
                lead.status = new_status
                lead.colaborador_id = colaborador_id
                lead.save(update_fields=["status", "colaborador_id", "updated_at"])

            elif old_status == "novo" and new_status == "em_contato":
                canal = (request.POST.get("canal") or "").strip()
                observacao = (request.POST.get("observacao") or "").strip()
                proximo_followup_s = (request.POST.get("proximo_followup") or "").strip()
                data_contato_s = (request.POST.get("data_contato") or "").strip()
                if canal not in canal_values:
                    return JsonResponse({"ok": False, "error": "validation", "message": "Canal inválido."}, status=400)
                if not observacao:
                    return JsonResponse(
                        {"ok": False, "error": "validation", "message": "Descreva o que foi conversado."},
                        status=400,
                    )
                pf = _parse_date_required(proximo_followup_s)
                if not pf:
                    return JsonResponse(
                        {"ok": False, "error": "validation", "message": "Próximo follow-up inválido."},
                        status=400,
                    )
                dt = _parse_datetime_local(data_contato_s)
                if not dt:
                    return JsonResponse(
                        {"ok": False, "error": "validation", "message": "Data do contato inválida."},
                        status=400,
                    )
                contato = ContatoLead.objects.create(
                    lead=lead,
                    colaborador_id=colaborador_id,
                    data_contato=dt,
                    canal=canal,
                    descricao=observacao,
                    respondeu=False,
                )
                contato_ref = contato
                t_kwargs.update(
                    canal=canal,
                    data_contato=dt,
                    observacao=observacao,
                    proximo_followup=pf,
                    contato=contato_ref,
                )
                LeadTransicao.objects.create(**t_kwargs)
                lead.status = new_status
                lead.proximo_followup = pf
                lead.colaborador_id = colaborador_id
                lead.save(update_fields=["status", "proximo_followup", "colaborador_id", "updated_at"])

            elif old_status == "em_contato" and new_status == "proposta_enviada":
                canal = (request.POST.get("canal") or "").strip()
                produto = (request.POST.get("produto_servico") or "").strip()
                data_envio_s = (request.POST.get("data_envio_proposta") or "").strip()
                rv = (request.POST.get("respondeu") or "").strip().lower()
                if rv not in ("true", "false", "1", "0"):
                    return JsonResponse(
                        {"ok": False, "error": "validation", "message": "Informe se o lead respondeu ao contato."},
                        status=400,
                    )
                respondeu = rv in ("true", "1")
                if canal not in canal_values:
                    return JsonResponse({"ok": False, "error": "validation", "message": "Canal inválido."}, status=400)
                if not produto:
                    return JsonResponse(
                        {"ok": False, "error": "validation", "message": "Produto/serviço apresentado é obrigatório."},
                        status=400,
                    )
                d_envio = _parse_date_required(data_envio_s)
                if not d_envio:
                    return JsonResponse(
                        {"ok": False, "error": "validation", "message": "Data de envio da proposta inválida."},
                        status=400,
                    )
                t_kwargs.update(
                    canal=canal,
                    respondeu=respondeu,
                    produto_servico=produto,
                    data_envio_proposta=d_envio,
                )
                LeadTransicao.objects.create(**t_kwargs)
                lead.status = new_status
                lead.colaborador_id = colaborador_id
                lead.save(update_fields=["status", "colaborador_id", "updated_at"])

            elif old_status == "proposta_enviada" and new_status == "convertido":
                produto = (request.POST.get("produto_servico") or "").strip()
                observacao = (request.POST.get("observacao") or "").strip()
                data_conv_s = (request.POST.get("data_conversao") or "").strip()
                d_conv = _parse_date_required(data_conv_s)
                if not d_conv:
                    return JsonResponse(
                        {"ok": False, "error": "validation", "message": "Data da conversão inválida."},
                        status=400,
                    )
                if not produto:
                    return JsonResponse(
                        {"ok": False, "error": "validation", "message": "Produto/serviço contratado é obrigatório."},
                        status=400,
                    )
                if not observacao:
                    return JsonResponse(
                        {"ok": False, "error": "validation", "message": "Observações finais são obrigatórias."},
                        status=400,
                    )
                t_kwargs.update(
                    data_conversao=d_conv,
                    produto_servico=produto,
                    observacao=observacao,
                )
                LeadTransicao.objects.create(**t_kwargs)
                lead.status = new_status
                lead.colaborador_id = colaborador_id
                lead.save(update_fields=["status", "colaborador_id", "updated_at"])

            else:
                return JsonResponse({"ok": False, "error": "rule", "message": "Combinação de etapas não suportada."}, status=400)

    except Exception as exc:
        return JsonResponse(
            {"ok": False, "error": "server", "message": f"Erro ao gravar: {exc!s}"},
            status=500,
        )

    return JsonResponse({"ok": True, "status": new_status})


def lead_list(request):
    leads = LeadEvento.objects.select_related(
        "evento",
        "categoria_profissional",
        "especialidade",
        "fase_academica",
        "estado_local",
        "cidade_local",
    ).all()

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    nivel = request.GET.get("nivel", "").strip()
    evento_id = request.GET.get("evento_id", "").strip()
    colaborador_id = request.GET.get("colaborador_id", "").strip()
    data_inicio = request.GET.get("data_inicio", "").strip()
    data_fim = request.GET.get("data_fim", "").strip()
    ordenacao = request.GET.get("ordenacao", "-updated_at").strip() or "-updated_at"

    if q:
        leads = leads.filter(nome__icontains=q)
    if status:
        leads = leads.filter(status=status)
    if nivel:
        leads = leads.filter(nivel_interesse=nivel)
    if evento_id:
        leads = leads.filter(evento_id=evento_id)
    if colaborador_id:
        leads = leads.filter(colaborador_id=colaborador_id)
    if data_inicio:
        leads = leads.filter(data_captacao__gte=data_inicio)
    if data_fim:
        leads = leads.filter(data_captacao__lte=data_fim)

    allowed_ordering = {"-updated_at", "updated_at", "-data_captacao", "data_captacao", "-score", "score"}
    if ordenacao not in allowed_ordering:
        ordenacao = "-updated_at"
    leads = leads.order_by(ordenacao)

    eventos = LeadEvento.objects.select_related("evento").values("evento_id", "evento__nome").distinct().order_by("evento__nome")
    context = {
        "leads": leads,
        "eventos": eventos,
        "status_choices": LeadEvento.StatusLead.choices,
        "nivel_choices": LeadEvento.NivelInteresse.choices,
        "filtros": {
            "q": q,
            "status": status,
            "nivel": nivel,
            "evento_id": evento_id,
            "colaborador_id": colaborador_id,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "ordenacao": ordenacao,
        },
    }
    return render(request, "leads/lead_list.html", context)


def lead_create(request):
    student_categories = CategoriaProfissional.objects.filter(
        nome__in=["Estudante de Medicina", "Estudante da Área da Saúde", "Estudante da Area da Saude"]
    )
    if request.method == "POST":
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lead-list")
    else:
        form = LeadForm()

    context = {
        "form": form,
        "student_category_ids": [item.id for item in student_categories],
        "is_edit": False,
    }
    return render(request, "leads/lead_create.html", context)


def lead_update(request, lead_id):
    student_categories = CategoriaProfissional.objects.filter(
        nome__in=["Estudante de Medicina", "Estudante da Área da Saúde", "Estudante da Area da Saude"]
    )
    lead = get_object_or_404(LeadEvento, pk=lead_id)
    if request.method == "POST":
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, "Lead atualizado com sucesso.")
            return redirect("kanban-board")
    else:
        form = LeadForm(instance=lead)

    return render(
        request,
        "leads/lead_create.html",
        {
            "form": form,
            "student_category_ids": [item.id for item in student_categories],
            "is_edit": True,
        },
    )


def lead_detail(request, lead_id):
    lead = get_object_or_404(
        LeadEvento.objects.select_related(
            "evento",
            "categoria_profissional",
            "especialidade",
            "fase_academica",
            "estado_local",
            "cidade_local",
        ),
        pk=lead_id,
    )
    contatos = ContatoLead.objects.filter(lead_id=lead.id).order_by("-data_contato")
    contato_initial = {}
    if lead.colaborador_id is not None:
        contato_initial["colaborador_id"] = lead.colaborador_id
    form = ContatoLeadForm(initial=contato_initial)
    return render(
        request,
        "leads/lead_detail.html",
        {"lead": lead, "contatos": contatos, "contato_form": form},
    )


@require_POST
def contato_create(request, lead_id):
    lead = get_object_or_404(LeadEvento, pk=lead_id)
    form = ContatoLeadForm(request.POST)
    if form.is_valid():
        contato = form.save(commit=False)
        contato.lead = lead
        contato.save()
        messages.success(request, "Contato registrado com sucesso.")
        return redirect("lead-detail", lead_id=lead.id)

    contatos = ContatoLead.objects.filter(lead_id=lead.id).order_by("-data_contato")
    return render(
        request,
        "leads/lead_detail.html",
        {"lead": lead, "contatos": contatos, "contato_form": form},
        status=400,
    )


def catalogos(request):
    _ensure_catalog_permission(request)
    context = {
        "total_categorias": CategoriaProfissional.objects.count(),
        "total_especialidades": Especialidade.objects.count(),
        "total_fases_academicas": FaseAcademica.objects.count(),
        "total_eventos": Evento.objects.count(),
    }
    return render(request, "leads/catalogos_home.html", context)


def _catalog_crud_page(
    request,
    model,
    form_class,
    template_name,
    context_object_name,
    success_create_message,
    page_title,
    use_outros_last=True,
    duplicate_error_message="Já existe um registro com estes dados.",
):
    _ensure_catalog_permission(request)
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if _save_form_commit_with_integrity_handling(
            request, form, duplicate_message=duplicate_error_message
        ):
            messages.success(request, success_create_message)
            return redirect(request.path)

    objects = _with_outros_last(model.objects.all()) if use_outros_last else model.objects.all()
    can_delete = _can_delete_catalog(request)
    return render(
        request,
        template_name,
        {
            "form": form,
            context_object_name: objects,
            "page_title": page_title,
            "can_delete": can_delete,
        },
    )


def categoria_profissional_crud(request):
    return _catalog_crud_page(
        request,
        CategoriaProfissional,
        CategoriaProfissionalCreateForm,
        "leads/catalog_categoria.html",
        "categorias",
        "Categoria cadastrada com sucesso.",
        "CRUD Categoria Profissional",
        duplicate_error_message="Já existe uma categoria profissional com este nome.",
    )


def especialidade_crud(request):
    _ensure_catalog_permission(request)
    form = EspecialidadeCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if _save_form_commit_with_integrity_handling(
            request,
            form,
            duplicate_message=(
                "Já existe uma especialidade com este nome para a categoria selecionada."
            ),
        ):
            messages.success(request, "Especialidade cadastrada com sucesso.")
            categoria_filtro = request.GET.get("categoria_profissional", "").strip()
            if categoria_filtro:
                return redirect(
                    f"{reverse('catalog-especialidade')}?categoria_profissional={categoria_filtro}"
                )
            return redirect("catalog-especialidade")

    categoria_filtro = request.GET.get("categoria_profissional", "").strip()
    qs = Especialidade.objects.select_related("categoria_profissional").all()
    if categoria_filtro.isdigit():
        qs = qs.filter(categoria_profissional_id=int(categoria_filtro))
    especialidades = _with_outros_last(qs)
    categorias_filtro = _with_outros_last(CategoriaProfissional.objects.filter(ativo=True))
    can_delete = _can_delete_catalog(request)
    return render(
        request,
        "leads/catalog_especialidade.html",
        {
            "form": form,
            "especialidades": especialidades,
            "page_title": "CRUD Especialidade",
            "can_delete": can_delete,
            "categorias_filtro": categorias_filtro,
            "filtro_categoria_id": categoria_filtro,
        },
    )


def evento_crud(request):
    _ensure_catalog_permission(request)
    form = EventoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if _save_form_commit_with_integrity_handling(
            request,
            form,
            duplicate_message="Já existe um evento cadastrado com estes dados.",
        ):
            messages.success(request, "Evento cadastrado com sucesso.")
            return redirect(request.path)
    eventos = Evento.objects.select_related("estado_local", "cidade_local").order_by("-data_evento", "-id")
    can_delete = _can_delete_catalog(request)
    return render(
        request,
        "leads/catalog_evento.html",
        {
            "form": form,
            "eventos": eventos,
            "page_title": "CRUD Evento",
            "can_delete": can_delete,
        },
    )


def fase_academica_crud(request):
    return _catalog_crud_page(
        request,
        FaseAcademica,
        FaseAcademicaCreateForm,
        "leads/catalog_fase_academica.html",
        "fases_academicas",
        "Fase acadêmica cadastrada com sucesso.",
        "CRUD Fase Acadêmica",
        use_outros_last=False,
        duplicate_error_message=(
            "Já existe uma fase acadêmica com esta combinação de nome e tipo."
        ),
    )


def categoria_profissional_update(request, pk):
    _ensure_catalog_permission(request)
    obj = get_object_or_404(CategoriaProfissional, pk=pk)
    form = CategoriaProfissionalEditForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        if _save_form_commit_with_integrity_handling(
            request,
            form,
            duplicate_message="Já existe uma categoria profissional com este nome.",
        ):
            messages.success(request, "Categoria atualizada com sucesso.")
            return redirect("catalog-categoria")
    return render(request, "leads/catalog_edit.html", {"form": form, "title": "Editar categoria profissional"})


def especialidade_update(request, pk):
    _ensure_catalog_permission(request)
    obj = get_object_or_404(Especialidade, pk=pk)
    form = EspecialidadeEditForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        if _save_form_commit_with_integrity_handling(
            request,
            form,
            duplicate_message=(
                "Já existe uma especialidade com este nome para a categoria selecionada."
            ),
        ):
            messages.success(request, "Especialidade atualizada com sucesso.")
            return redirect("catalog-especialidade")
    return render(request, "leads/catalog_edit.html", {"form": form, "title": "Editar especialidade"})


def evento_update(request, pk):
    _ensure_catalog_permission(request)
    obj = get_object_or_404(Evento, pk=pk)
    form = EventoForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        if _save_form_commit_with_integrity_handling(
            request,
            form,
            duplicate_message="Já existe um evento cadastrado com estes dados.",
        ):
            messages.success(request, "Evento atualizado com sucesso.")
            return redirect("catalog-evento")
    return render(request, "leads/catalog_edit.html", {"form": form, "title": "Editar evento"})


def fase_academica_update(request, pk):
    _ensure_catalog_permission(request)
    obj = get_object_or_404(FaseAcademica, pk=pk)
    form = FaseAcademicaEditForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        if _save_form_commit_with_integrity_handling(
            request,
            form,
            duplicate_message=(
                "Já existe uma fase acadêmica com esta combinação de nome e tipo."
            ),
        ):
            messages.success(request, "Fase acadêmica atualizada com sucesso.")
            return redirect("catalog-fase-academica")
    return render(request, "leads/catalog_edit.html", {"form": form, "title": "Editar fase acadêmica"})


@require_POST
def categoria_profissional_delete(request, pk):
    _ensure_delete_permission(request)
    obj = get_object_or_404(CategoriaProfissional, pk=pk)
    obj.delete()
    messages.success(request, "Categoria removida com sucesso.")
    return redirect("catalog-categoria")


@require_POST
def especialidade_delete(request, pk):
    _ensure_delete_permission(request)
    obj = get_object_or_404(Especialidade, pk=pk)
    obj.delete()
    messages.success(request, "Especialidade removida com sucesso.")
    return redirect("catalog-especialidade")


@require_POST
def evento_delete(request, pk):
    _ensure_delete_permission(request)
    obj = get_object_or_404(Evento, pk=pk)
    obj.delete()
    messages.success(request, "Evento removido com sucesso.")
    return redirect("catalog-evento")


@require_POST
def fase_academica_delete(request, pk):
    _ensure_delete_permission(request)
    obj = get_object_or_404(FaseAcademica, pk=pk)
    obj.delete()
    messages.success(request, "Fase acadêmica removida com sucesso.")
    return redirect("catalog-fase-academica")


def api_especialidades_por_categoria(request):
    categoria_id = request.GET.get("categoria_id")
    if not categoria_id:
        return JsonResponse({"results": []})
    especialidades = (
        Especialidade.objects.filter(categoria_profissional_id=categoria_id, ativo=True)
        .annotate(
            _sort_nao=Case(
                When(nome__iexact="Não informado", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("_sort_nao", "nome")
    )
    return JsonResponse({"results": [{"id": item.id, "nome": item.nome} for item in especialidades]})


def api_estados(_request):
    estados = Estado.objects.all().order_by("nome")
    return JsonResponse(
        {"results": [{"id": e.id, "nome": f"{e.nome} ({e.uf})", "uf": e.uf} for e in estados]}
    )


def api_cidades(request):
    estado_id = request.GET.get("estado_id", "").strip()
    if not estado_id.isdigit():
        return JsonResponse({"results": []})
    cidades = Cidade.objects.filter(estado_id=int(estado_id)).order_by("nome")
    return JsonResponse({"results": [{"id": c.id, "nome": c.nome} for c in cidades]})
