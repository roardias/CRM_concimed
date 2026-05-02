from calendar import monthrange
from datetime import date, timedelta

from django.db.models import CharField, Count, F, Q, Value
from django.db.models.functions import Coalesce
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from leads.models import LeadEvento

MESES_CURTO = (
    "",
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)

MESES_LONGO = (
    "",
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def _month_start(y: int, m: int) -> date:
    return date(y, m, 1)


def _last_day_of_month(y: int, m: int) -> date:
    return date(y, m, monthrange(y, m)[1])


def _iter_last_n_calendar_months(n: int, end: date):
    y, m = end.year, end.month
    keys = []
    for _ in range(n):
        keys.append((y, m))
        m -= 1
        if m < 1:
            m = 12
            y -= 1
    keys.reverse()
    return keys


def _month_key_from_trunc(val):
    if val is None:
        return None
    if hasattr(val, "year") and hasattr(val, "month"):
        return (val.year, val.month)
    return None


def dashboard(request):
    today = timezone.localdate()
    now_dt = timezone.now()

    # --- Janelas de tempo: últimos 30 dias vs 30 dias anteriores
    end_30 = today
    start_30 = today - timedelta(days=29)
    start_prev_30 = start_30 - timedelta(days=30)
    end_prev_30 = start_30 - timedelta(days=1)

    leads_30d = LeadEvento.objects.filter(
        data_captacao__gte=start_30, data_captacao__lte=end_30
    ).count()
    leads_prev_30d = LeadEvento.objects.filter(
        data_captacao__gte=start_prev_30, data_captacao__lte=end_prev_30
    ).count()
    if leads_prev_30d > 0:
        kpi_trend_pct = round((leads_30d - leads_prev_30d) / leads_prev_30d * 100, 1)
    else:
        kpi_trend_pct = None

    convertidos_30d = LeadEvento.objects.filter(
        data_captacao__gte=start_30,
        data_captacao__lte=end_30,
        status=LeadEvento.StatusLead.CONVERTIDO,
    ).count()
    conv_rate_30d = (
        round(convertidos_30d / leads_30d * 100, 1) if leads_30d else 0.0
    )

    # Mês calendário atual (captação)
    cur_y, cur_m = today.year, today.month
    month_start = _month_start(cur_y, cur_m)
    month_end = _last_day_of_month(cur_y, cur_m)
    captacao_mes_atual = LeadEvento.objects.filter(
        data_captacao__gte=month_start, data_captacao__lte=month_end
    ).count()

    # Pipeline atual (em qualificação)
    em_qualificacao = LeadEvento.objects.filter(
        status__in=[
            LeadEvento.StatusLead.EM_CONTATO,
            LeadEvento.StatusLead.PROPOSTA_ENVIADA,
        ]
    ).count()

    # --- Série mensal (6 meses): total captado vs convertidos (na base, status atual)
    month_keys = _iter_last_n_calendar_months(6, today)
    chart_labels = [f"{MESES_CURTO[m]}/{str(y)[2:]}" for y, m in month_keys]
    start_bound = _month_start(month_keys[0][0], month_keys[0][1])

    monthly_qs = (
        LeadEvento.objects.filter(data_captacao__gte=start_bound)
        .annotate(m=TruncMonth("data_captacao"))
        .values("m")
        .annotate(
            total=Count("id"),
            convertidos=Count(
                "id", filter=Q(status=LeadEvento.StatusLead.CONVERTIDO)
            ),
        )
    )
    agg_by_month = {}
    for row in monthly_qs:
        key = _month_key_from_trunc(row["m"])
        if key:
            agg_by_month[key] = {
                "total": row["total"],
                "convertidos": row["convertidos"],
            }

    chart_totals = []
    chart_convertidos = []
    for y, m in month_keys:
        cell = agg_by_month.get((y, m), {"total": 0, "convertidos": 0})
        chart_totals.append(cell["total"])
        chart_convertidos.append(cell["convertidos"])

    chart_line = {
        "labels": chart_labels,
        "totals": chart_totals,
        "convertidos": chart_convertidos,
    }

    # --- Funil (etapas principais, sem perdido)
    funnel_order = [
        (LeadEvento.StatusLead.NOVO, "Novo"),
        (LeadEvento.StatusLead.EM_CONTATO, "Em contato"),
        (LeadEvento.StatusLead.PROPOSTA_ENVIADA, "Proposta"),
        (LeadEvento.StatusLead.CONVERTIDO, "Convertido"),
    ]
    funnel_counts = []
    for val, _ in funnel_order:
        funnel_counts.append(
            LeadEvento.objects.filter(status=val).count()
        )
    funnel_steps = []
    funnel_colors = ["#2563eb", "#ea580c", "#7c3aed", "#16a34a"]
    prev = None
    for i, ((val, label), count, color) in enumerate(
        zip(funnel_order, funnel_counts, funnel_colors, strict=True)
    ):
        if i == 0:
            pct_prev = 100.0 if count else 0.0
        elif prev and prev > 0:
            pct_prev = round(count / prev * 100, 1)
        else:
            pct_prev = 0.0
        funnel_steps.append(
            {
                "label": label,
                "count": count,
                "pct_prev": pct_prev,
                "color": color,
            }
        )
        prev = count

    total_funil_top = funnel_counts[0] or 1
    conversao_geral_pct = (
        round(funnel_counts[-1] / total_funil_top * 100, 1) if total_funil_top else 0.0
    )

    # --- Captação por evento (top 8)
    por_evento = list(
        LeadEvento.objects.values("evento_id", "evento__nome")
        .annotate(
            total=Count("id"),
            convertidos=Count(
                "id", filter=Q(status=LeadEvento.StatusLead.CONVERTIDO)
            ),
        )
        .order_by("-total")[:8]
    )
    chart_eventos = {
        "labels": [r["evento__nome"] or "—" for r in por_evento],
        "totals": [r["total"] for r in por_evento],
        "convertidos": [r["convertidos"] for r in por_evento],
    }

    # --- Por categoria (donut): inclui leads sem categoria como "Sem categoria"
    por_categoria = list(
        LeadEvento.objects.annotate(
            cat_nome=Coalesce(
                F("categoria_profissional__nome"),
                Value("Sem categoria", output_field=CharField()),
            )
        )
        .values("cat_nome")
        .annotate(c=Count("id"))
        .order_by("-c")[:12]
    )
    chart_categorias = {
        "labels": [r["cat_nome"] or "—" for r in por_categoria],
        "data": [r["c"] for r in por_categoria],
    }

    # --- Top especialidades
    por_especialidade = list(
        LeadEvento.objects.exclude(especialidade__isnull=True)
        .values("especialidade__nome")
        .annotate(c=Count("id"))
        .order_by("-c")[:8]
    )
    max_esp = max((r["c"] for r in por_especialidade), default=1)
    esp_colors = [
        "#2563eb",
        "#16a34a",
        "#7c3aed",
        "#ea580c",
        "#dc2626",
        "#0891b2",
        "#ca8a04",
        "#4f46e5",
    ]
    top_especialidades = []
    for i, row in enumerate(por_especialidade):
        top_especialidades.append(
            {
                "nome": row["especialidade__nome"] or "—",
                "count": row["c"],
                "pct": round(row["c"] / max_esp * 100, 1),
                "color": esp_colors[i % len(esp_colors)],
            }
        )

    # --- Snapshot por status (4 etapas do funil; % sobre leads não perdidos)
    leads_nao_perdido = LeadEvento.objects.exclude(
        status=LeadEvento.StatusLead.PERDIDO
    ).count()
    snapshot_status = []
    for val, label in funnel_order:
        c = LeadEvento.objects.filter(status=val).count()
        pct = (
            round(c / leads_nao_perdido * 100, 1) if leads_nao_perdido else 0.0
        )
        snapshot_status.append(
            {
                "value": val,
                "label": label,
                "count": c,
                "pct_total": pct,
                "color": funnel_colors[len(snapshot_status) % len(funnel_colors)],
            }
        )

    latest_leads = (
        LeadEvento.objects.select_related("evento")
        .order_by("-updated_at")[:5]
    )

    return render(
        request,
        "core/dashboard.html",
        {
            "kpi_leads_periodo": leads_30d,
            "kpi_trend_pct": kpi_trend_pct,
            "kpi_convertidos": convertidos_30d,
            "kpi_conv_rate": conv_rate_30d,
            "kpi_em_qualificacao": em_qualificacao,
            "kpi_captacao_mes": captacao_mes_atual,
            "kpi_mes_nome": MESES_LONGO[today.month],
            "chart_line": chart_line,
            "funnel_steps": funnel_steps,
            "conversao_geral_pct": conversao_geral_pct,
            "chart_eventos": chart_eventos,
            "chart_categorias": chart_categorias,
            "top_especialidades": top_especialidades,
            "snapshot_status": snapshot_status,
            "latest_leads": latest_leads,
            "now_year": now_dt.year,
        },
    )
