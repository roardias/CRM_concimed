from django import forms
from django.db.models import Case, IntegerField, Value, When

from .models import (
    CategoriaProfissional,
    Cidade,
    ContatoLead,
    Especialidade,
    Estado,
    Evento,
    FaseAcademica,
    LeadEvento,
    STUDENT_PROFESSIONAL_CATEGORY_NAMES,
    especialidade_eh_nao_informada,
    tipo_lead_for_categoria,
)


def _sync_localizacao_campos_texto(obj):
    is_lead = isinstance(obj, LeadEvento)
    if obj.cidade_local_id:
        c = Cidade.objects.select_related("estado").get(pk=obj.cidade_local_id)
        obj.cidade = c.nome
        obj.estado = c.estado.uf
        obj.estado_local_id = c.estado_id
    elif getattr(obj, "estado_local_id", None):
        obj.estado = Estado.objects.get(pk=obj.estado_local_id).uf
        if is_lead:
            obj.cidade = None
        else:
            obj.cidade = ""
    else:
        if is_lead:
            obj.cidade = None
            obj.estado = None
        else:
            obj.cidade = ""
            obj.estado = ""


def _with_outros_last(queryset):
    return queryset.annotate(
        outros_last=Case(
            When(nome__iexact="Outros", then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by("outros_last", "nome")


class LeadForm(forms.ModelForm):
    class Meta:
        model = LeadEvento
        fields = [
            "nome",
            "email",
            "telefone",
            "instagram",
            "linkedin",
            "tiktok",
            "youtube",
            "categoria_profissional",
            "especialidade",
            "fase_academica",
            "instituicao",
            "semestre",
            "ano_formatura",
            "conselho_registro",
            "registro_profissional",
            "estado_local",
            "cidade_local",
            "evento",
            "colaborador_id",
            "status",
            "nivel_interesse",
            "score",
            "proximo_followup",
            "data_captacao",
            "aceite_lgpd",
            "aceita_comunicacao",
            "observacoes",
        ]
        widgets = {
            "telefone": forms.TextInput(
                attrs={
                    "type": "tel",
                    "placeholder": "(11) 9 9999 9999",
                    "maxlength": "19",
                    "autocomplete": "tel",
                    "inputmode": "numeric",
                }
            ),
            "proximo_followup": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "data_captacao": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "instagram": forms.TextInput(
                attrs={"placeholder": "Instagram (link ou @usuario)", "maxlength": "500", "autocomplete": "off"}
            ),
            "linkedin": forms.TextInput(
                attrs={"placeholder": "LinkedIn (URL ou perfil)", "maxlength": "500", "autocomplete": "off"}
            ),
            "tiktok": forms.TextInput(
                attrs={"placeholder": "TikTok (link ou @usuario)", "maxlength": "500", "autocomplete": "off"}
            ),
            "youtube": forms.TextInput(
                attrs={"placeholder": "YouTube (link ou canal)", "maxlength": "500", "autocomplete": "off"}
            ),
        }
        labels = {
            "instagram": "Instagram",
            "linkedin": "LinkedIn",
            "tiktok": "TikTok",
            "youtube": "YouTube",
            "categoria_profissional": "Categoria profissional",
            "especialidade": "Especialidade (opcional no cadastro)",
            "fase_academica": "Fase acadêmica",
            "conselho_registro": "Conselho de registro",
            "registro_profissional": "Registro profissional",
            "proximo_followup": "Próximo follow-up",
            "data_captacao": "Data de captação",
            "aceite_lgpd": "Aceite LGPD",
            "aceita_comunicacao": "Aceita comunicação",
            "observacoes": "Observações",
            "estado_local": "Estado",
            "cidade_local": "Município",
            "colaborador_id": "Colaborador (comercial)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _date_name in ("data_captacao", "proximo_followup"):
            if _date_name in self.fields:
                f = self.fields[_date_name]
                f.widget.format = "%Y-%m-%d"
                f.input_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
        self.fields["estado_local"].queryset = Estado.objects.all()
        self.fields["estado_local"].required = False
        self.fields["cidade_local"].required = False
        self.fields["especialidade"].required = False
        self.fields["colaborador_id"].required = False
        self.fields["colaborador_id"].help_text = "Opcional no cadastro; pode ser definido depois ao direcionar o lead."
        for _name in ("instagram", "linkedin", "tiktok", "youtube"):
            self.fields[_name].required = False
        estado_id = None
        if self.is_bound:
            estado_id = self.data.get("estado_local") or None
        elif self.instance and self.instance.pk:
            estado_id = self.instance.estado_local_id
        if estado_id:
            self.fields["cidade_local"].queryset = Cidade.objects.filter(estado_id=estado_id).order_by("nome")
        else:
            self.fields["cidade_local"].queryset = Cidade.objects.none()

        self.fields["categoria_profissional"].queryset = _with_outros_last(CategoriaProfissional.objects.filter(ativo=True))
        self.fields["especialidade"].queryset = Especialidade.objects.none()
        self.fields["fase_academica"].queryset = FaseAcademica.objects.filter(
            ativo=True, tipo=FaseAcademica.TipoFase.SEMESTRE
        ).order_by("ordem", "nome")
        self.fields["fase_academica"].required = False

        categoria_id = None
        if self.is_bound:
            categoria_id = self.data.get("categoria_profissional") or None
        elif self.instance and self.instance.pk:
            categoria_id = self.instance.categoria_profissional_id

        if categoria_id:
            self.fields["especialidade"].queryset = _with_outros_last(
                Especialidade.objects.filter(categoria_profissional_id=categoria_id, ativo=True)
            )

    def clean_telefone(self):
        raw = (self.cleaned_data.get("telefone") or "").strip()
        digits = "".join(ch for ch in raw if ch.isdigit())
        if not digits:
            return ""
        if len(digits) != 11 or digits[2] != "9":
            raise forms.ValidationError(
                "Telefone deve ter 11 dígitos (2 do DDD + 9 do número). O primeiro dígito após o DDD deve ser 9."
            )
        return digits

    def clean_colaborador_id(self):
        v = self.cleaned_data.get("colaborador_id")
        if v in (None, ""):
            return None
        return v

    def clean(self):
        cleaned_data = super().clean()
        categoria = cleaned_data.get("categoria_profissional")
        especialidade = cleaned_data.get("especialidade")

        if not categoria:
            self.add_error("categoria_profissional", "Categoria profissional é obrigatória.")
            return cleaned_data

        is_student_category = categoria and categoria.nome.strip().lower() in STUDENT_PROFESSIONAL_CATEGORY_NAMES

        if is_student_category:
            if especialidade and not especialidade_eh_nao_informada(especialidade):
                self.add_error(
                    "especialidade",
                    "Para estudantes, em especialidade use apenas «Não informado» ou deixe vazio.",
                )
                cleaned_data["especialidade"] = None
            elif not especialidade:
                cleaned_data["especialidade"] = None
            if not cleaned_data.get("fase_academica"):
                self.add_error("fase_academica", "Fase acadêmica é obrigatória para esta categoria.")
        else:
            cleaned_data["fase_academica"] = None

        if (
            categoria
            and especialidade
            and especialidade.categoria_profissional_id != categoria.id
        ):
            self.add_error("especialidade", "A especialidade selecionada não pertence à categoria escolhida.")

        est = cleaned_data.get("estado_local")
        cid = cleaned_data.get("cidade_local")
        if cid and est and cid.estado_id != est.id:
            self.add_error("cidade_local", "O município não pertence ao estado selecionado.")
        if cid and not est:
            self.add_error("estado_local", "Selecione o estado do município.")

        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.tipo_lead = tipo_lead_for_categoria(obj.categoria_profissional)
        _sync_localizacao_campos_texto(obj)
        if commit:
            obj.save()
        return obj


class ContatoLeadForm(forms.ModelForm):
    class Meta:
        model = ContatoLead
        fields = ["colaborador_id", "data_contato", "canal", "descricao", "respondeu"]
        widgets = {
            "data_contato": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
        labels = {
            "data_contato": "Data do contato",
            "descricao": "Descrição",
            "respondeu": "Respondeu",
        }


class CategoriaProfissionalCreateForm(forms.ModelForm):
    class Meta:
        model = CategoriaProfissional
        fields = ["nome", "descricao"]
        labels = {"descricao": "Descrição"}


class CategoriaProfissionalEditForm(forms.ModelForm):
    class Meta:
        model = CategoriaProfissional
        fields = ["nome", "descricao", "ativo"]
        labels = {"descricao": "Descrição", "ativo": "Ativo"}


class EspecialidadeCreateForm(forms.ModelForm):
    class Meta:
        model = Especialidade
        fields = ["categoria_profissional", "nome", "descricao"]
        labels = {
            "categoria_profissional": "Categoria profissional",
            "descricao": "Descrição",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria_profissional"].queryset = _with_outros_last(CategoriaProfissional.objects.filter(ativo=True))


class EspecialidadeEditForm(forms.ModelForm):
    class Meta:
        model = Especialidade
        fields = ["categoria_profissional", "nome", "descricao", "ativo"]
        labels = {
            "categoria_profissional": "Categoria profissional",
            "descricao": "Descrição",
            "ativo": "Ativo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria_profissional"].queryset = _with_outros_last(CategoriaProfissional.objects.filter(ativo=True))


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ["nome", "tipo", "local", "estado_local", "cidade_local", "data_evento", "data_fim"]
        widgets = {
            "data_evento": forms.DateInput(attrs={"type": "date"}),
            "data_fim": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "data_evento": "Data de início",
            "data_fim": "Data de término",
            "estado_local": "Estado",
            "cidade_local": "Município",
        }
        help_texts = {
            "data_fim": "Opcional. Deixe em branco se o evento for em um único dia.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estado_local"].queryset = Estado.objects.all()
        estado_id = None
        if self.is_bound:
            estado_id = self.data.get("estado_local") or None
        elif self.instance and self.instance.pk:
            estado_id = self.instance.estado_local_id
        if estado_id:
            self.fields["cidade_local"].queryset = Cidade.objects.filter(estado_id=estado_id).order_by("nome")
        else:
            self.fields["cidade_local"].queryset = Cidade.objects.none()

    def clean(self):
        cleaned = super().clean()
        ini = cleaned.get("data_evento")
        fim = cleaned.get("data_fim")
        if ini and fim:
            if fim < ini:
                self.add_error("data_fim", "A data de término não pode ser anterior à data de início.")
            elif fim == ini:
                cleaned["data_fim"] = None
        est = cleaned.get("estado_local")
        cid = cleaned.get("cidade_local")
        if not est or not cid:
            self.add_error("estado_local", "Estado e município são obrigatórios.")
        elif cid.estado_id != est.id:
            self.add_error("cidade_local", "O município não pertence ao estado selecionado.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        _sync_localizacao_campos_texto(obj)
        if commit:
            obj.save()
        return obj


class FaseAcademicaCreateForm(forms.ModelForm):
    class Meta:
        model = FaseAcademica
        fields = ["nome", "tipo", "ordem"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sem = FaseAcademica.TipoFase.SEMESTRE
        self.fields["tipo"].choices = [(sem.value, sem.label)]
        self.fields["tipo"].initial = sem.value


class FaseAcademicaEditForm(forms.ModelForm):
    class Meta:
        model = FaseAcademica
        fields = ["nome", "tipo", "ordem", "ativo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sem = FaseAcademica.TipoFase.SEMESTRE
        self.fields["tipo"].choices = [(sem.value, sem.label)]
