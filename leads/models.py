from django.db import models

# Nomes de categoria para os quais a fase acadêmica é obrigatória (especialidade: vazio ou "Não informado").
STUDENT_PROFESSIONAL_CATEGORY_NAMES = frozenset(
    {
        "estudante de medicina",
        "estudante da área da saúde",
        "estudante da area da saude",
    }
)

# Especialidade sintética por categoria (nome único no seed SQL).
NAO_INFORMADO_ESPECIALIDADE_NAMES = frozenset({"não informado", "nao informado"})


def especialidade_eh_nao_informada(especialidade) -> bool:
    if not especialidade:
        return False
    nome = (getattr(especialidade, "nome", None) or "").strip().lower()
    return nome in NAO_INFORMADO_ESPECIALIDADE_NAMES


class Estado(models.Model):
    id = models.IntegerField(primary_key=True)
    nome = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)
    regiao = models.CharField(max_length=20)

    class Meta:
        db_table = "concimed_estado"
        managed = False
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.uf})"


class Cidade(models.Model):
    id = models.IntegerField(primary_key=True)
    estado = models.ForeignKey(
        Estado,
        on_delete=models.PROTECT,
        db_column="estado_id",
        related_name="cidades",
    )
    nome = models.CharField(max_length=120)

    class Meta:
        db_table = "concimed_cidade"
        managed = False
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class CategoriaProfissional(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=120)
    descricao = models.CharField(max_length=255, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "concimed_categoria_profissional"
        managed = False
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Profissao(models.Model):
    id = models.BigAutoField(primary_key=True)
    categoria_profissional = models.ForeignKey(
        CategoriaProfissional,
        on_delete=models.PROTECT,
        db_column="categoria_profissional_id",
        related_name="profissoes",
    )
    nome = models.CharField(max_length=120)
    descricao = models.CharField(max_length=255, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "concimed_profissao"
        managed = False
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Especialidade(models.Model):
    id = models.BigAutoField(primary_key=True)
    categoria_profissional = models.ForeignKey(
        CategoriaProfissional,
        on_delete=models.PROTECT,
        db_column="categoria_profissional_id",
        related_name="especialidades",
    )
    nome = models.CharField(max_length=120)
    descricao = models.CharField(max_length=255, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "concimed_especialidade"
        managed = False
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class FaseAcademica(models.Model):
    class TipoFase(models.TextChoices):
        SEMESTRE = "SEMESTRE", "Semestre"
        INTERNATO = "INTERNATO", "Internato"
        RESIDENCIA = "RESIDENCIA", "Residência"

    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=50)
    tipo = models.CharField(max_length=30, choices=TipoFase.choices)
    ordem = models.IntegerField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "concimed_fases_academicas"
        managed = False
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome


class Evento(models.Model):
    class TipoEvento(models.TextChoices):
        FEIRA = "feira", "Feira"
        EVENTO_FACULDADE = "evento_faculdade", "Evento de Faculdade"
        CONGRESSO = "congresso", "Congresso"
        OUTRO = "outro", "Outro"

    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TipoEvento.choices)
    local = models.CharField(max_length=200)
    cidade = models.CharField(max_length=120)
    estado = models.CharField(max_length=2)
    estado_local = models.ForeignKey(
        Estado,
        on_delete=models.PROTECT,
        db_column="estado_id",
        related_name="eventos",
        blank=True,
        null=True,
    )
    cidade_local = models.ForeignKey(
        Cidade,
        on_delete=models.PROTECT,
        db_column="cidade_id",
        related_name="eventos",
        blank=True,
        null=True,
    )
    data_evento = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    class Meta:
        db_table = "concimed_eventos"
        managed = False
        ordering = ["-data_evento", "-id"]


class LeadEvento(models.Model):
    class TipoLead(models.TextChoices):
        ESTUDANTE = "estudante", "Estudante"
        MEDICO = "medico", "Medico"
        OUTRO_PROFISSIONAL = "outro_profissional", "Outro Profissional"

    class StatusLead(models.TextChoices):
        NOVO = "novo", "Novo"
        EM_CONTATO = "em_contato", "Em Contato"
        PROPOSTA_ENVIADA = "proposta_enviada", "Proposta Enviada"
        CONVERTIDO = "convertido", "Convertido"
        PERDIDO = "perdido", "Perdido"

    class NivelInteresse(models.TextChoices):
        FRIO = "frio", "Frio"
        MORNO = "morno", "Morno"
        QUENTE = "quente", "Quente"

    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=180)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=30, blank=True, null=True)
    instagram = models.CharField(max_length=500, blank=True, null=True)
    linkedin = models.CharField(max_length=500, blank=True, null=True)
    tiktok = models.CharField(max_length=500, blank=True, null=True)
    youtube = models.CharField(max_length=500, blank=True, null=True)
    tipo_lead = models.CharField(max_length=20, choices=TipoLead.choices)
    especialidade_texto = models.CharField(max_length=120, blank=True, null=True, db_column="especialidade")
    categoria_profissional = models.ForeignKey(
        CategoriaProfissional,
        on_delete=models.PROTECT,
        db_column="categoria_profissional_id",
        related_name="leads",
        blank=True,
        null=True,
    )
    profissao = models.ForeignKey(  # legado, mantido para compatibilidade temporaria
        Profissao,
        on_delete=models.PROTECT,
        db_column="profissao_id",
        related_name="leads",
        blank=True,
        null=True,
    )
    especialidade = models.ForeignKey(
        Especialidade,
        on_delete=models.PROTECT,
        db_column="especialidade_id",
        related_name="leads",
        blank=True,
        null=True,
    )
    fase_academica = models.ForeignKey(
        FaseAcademica,
        on_delete=models.PROTECT,
        db_column="fase_academica_id",
        related_name="leads",
        blank=True,
        null=True,
    )
    instituicao = models.CharField(max_length=180, blank=True, null=True)
    semestre = models.PositiveSmallIntegerField(blank=True, null=True)
    ano_formatura = models.PositiveSmallIntegerField(blank=True, null=True)
    conselho_registro = models.CharField(max_length=20, blank=True, null=True)
    registro_profissional = models.CharField(max_length=40, blank=True, null=True)
    cidade = models.CharField(max_length=120, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    estado_local = models.ForeignKey(
        Estado,
        on_delete=models.PROTECT,
        db_column="estado_id",
        related_name="leads",
        blank=True,
        null=True,
    )
    cidade_local = models.ForeignKey(
        Cidade,
        on_delete=models.PROTECT,
        db_column="cidade_id",
        related_name="leads",
        blank=True,
        null=True,
    )
    evento = models.ForeignKey(Evento, on_delete=models.PROTECT, db_column="evento_id", related_name="leads")
    colaborador_id = models.BigIntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=StatusLead.choices, default=StatusLead.NOVO)
    nivel_interesse = models.CharField(max_length=10, choices=NivelInteresse.choices, default=NivelInteresse.FRIO)
    score = models.PositiveSmallIntegerField(default=0)
    proximo_followup = models.DateField(blank=True, null=True)
    data_captacao = models.DateField()
    aceite_lgpd = models.BooleanField(default=False)
    aceita_comunicacao = models.CharField(max_length=10, default="nenhum")
    observacoes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "concimed_leads_eventos"
        managed = False
        ordering = ["-updated_at"]

    def __str__(self):
        return self.nome

    @property
    def internato_implicito(self):
        """5º e 6º ano já incluem internato (sem fase separada). Válido para categorias de estudante."""
        if not self.categoria_profissional or not self.fase_academica:
            return False
        if self.categoria_profissional.nome.strip().lower() not in STUDENT_PROFESSIONAL_CATEGORY_NAMES:
            return False
        n = self.fase_academica.nome.strip().lower()
        # Pós-migração por semestres: 5º/6º ano → 10º/12º semestre (últimos anos com internato implícito).
        return n in {
            "10º semestre",
            "10o semestre",
            "12º semestre",
            "12o semestre",
            # Compatível com bases ainda não migradas:
            "5º ano",
            "5o ano",
            "6º ano",
            "6o ano",
        }


def tipo_lead_for_categoria(categoria_profissional):
    """
    Valores aceitos pela coluna tipo_lead (ENUM em MySQL: estudante, medico, outro_profissional).
    O formulário de lead não expõe tipo_lead; derivamos da categoria ao persistir.
    """
    if not categoria_profissional:
        return LeadEvento.TipoLead.OUTRO_PROFISSIONAL
    nome = (categoria_profissional.nome or "").strip().lower()
    if nome in STUDENT_PROFESSIONAL_CATEGORY_NAMES:
        return LeadEvento.TipoLead.ESTUDANTE
    if nome in ("médico", "medico"):
        return LeadEvento.TipoLead.MEDICO
    return LeadEvento.TipoLead.OUTRO_PROFISSIONAL


class ContatoLead(models.Model):
    class CanalContato(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"
        TELEFONE = "telefone", "Telefone"
        PRESENCIAL = "presencial", "Presencial"
        OUTRO = "outro", "Outro"

    id = models.BigAutoField(primary_key=True)
    lead = models.ForeignKey(LeadEvento, on_delete=models.PROTECT, db_column="lead_id", related_name="contatos")
    colaborador_id = models.BigIntegerField()
    data_contato = models.DateTimeField()
    canal = models.CharField(max_length=10, choices=CanalContato.choices)
    descricao = models.TextField()
    respondeu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "concimed_contatos"
        managed = False
        ordering = ["-data_contato", "-id"]


class LeadTransicao(models.Model):
    """Registro de cada mudança de etapa no Kanban (tabela concimed_lead_transicoes)."""

    class MotivoPerda(models.TextChoices):
        SEM_INTERESSE = "sem_interesse", "Sem interesse"
        SEM_RETORNO = "sem_retorno", "Sem retorno"
        ESCOLHEU_CONCORRENTE = "escolheu_concorrente", "Escolheu concorrente"
        MOMENTO_RUIM = "momento_ruim", "Momento ruim"
        OUTROS = "outros", "Outros"

    class CanalTransicao(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        TELEFONE = "telefone", "Telefone"
        EMAIL = "email", "E-mail"
        PRESENCIAL = "presencial", "Presencial"
        OUTRO = "outro", "Outro"

    id = models.BigAutoField(primary_key=True)
    lead = models.ForeignKey(
        LeadEvento,
        on_delete=models.PROTECT,
        db_column="lead_id",
        related_name="transicoes",
    )
    colaborador_id = models.BigIntegerField()
    etapa_anterior = models.CharField(max_length=20, choices=LeadEvento.StatusLead.choices)
    etapa_nova = models.CharField(max_length=20, choices=LeadEvento.StatusLead.choices)
    canal = models.CharField(max_length=10, choices=CanalTransicao.choices, blank=True, null=True)
    data_contato = models.DateTimeField(blank=True, null=True)
    respondeu = models.BooleanField(blank=True, null=True)
    produto_servico = models.CharField(max_length=255, blank=True, null=True)
    data_envio_proposta = models.DateField(blank=True, null=True)
    data_conversao = models.DateField(blank=True, null=True)
    motivo_perda = models.CharField(max_length=30, choices=MotivoPerda.choices, blank=True, null=True)
    observacao = models.TextField(blank=True, null=True)
    proximo_followup = models.DateField(blank=True, null=True)
    contato = models.ForeignKey(
        ContatoLead,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_column="contato_id",
        related_name="transicoes_kanban",
    )
    data_transicao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "concimed_lead_transicoes"
        managed = False
        ordering = ["-data_transicao", "-id"]
