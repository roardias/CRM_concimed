"""
Carga em massa de leads na tabela concimed_leads_eventos a partir de CSV.

Colunas esperadas (como no formulário / export Excel BR):
  Nome; Email; Instagran; Fase acadêmica; Telefone; Evento; Categoria profissional;
  Data de captação; Especialidade (opcional no cadastro)

Arquivo mestre em Carga_Leads/: Pasta2.csv (lista completa).

Uso (na raiz do projeto, com .env configurado):
  python scripts/carga_leads_csv.py
  python scripts/carga_leads_csv.py -i "Carga_Leads/Pasta2.csv"
  python scripts/carga_leads_csv.py -i arquivo.csv --dry-run
  python scripts/carga_leads_csv.py --encoding utf-8-sig --delimiter ,

Por padrão: encoding cp1252, delimitador ; (Excel Brasil).
Datas numéricas tipo 45978 são tratadas como serial Excel (origem 30/12/1899).
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import os
import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "concimed_crm.settings")
django.setup()

from django.db import DatabaseError, transaction

from leads.models import (
    CategoriaProfissional,
    Especialidade,
    Evento,
    FaseAcademica,
    LeadEvento,
    STUDENT_PROFESSIONAL_CATEGORY_NAMES,
    especialidade_eh_nao_informada,
    tipo_lead_for_categoria,
)


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _digits(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())


def normalize_phone(raw: str) -> str:
    d = _digits(raw)
    if not d:
        return ""
    # Planilha com DDI 55 (13 dígitos): 55 + DDD + 9 dígitos
    if d.startswith("55") and len(d) == 13:
        d = d[2:]
    if len(d) == 11 and d[2] == "9":
        return d
    return d


def parse_data_captacao(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw.isdigit() or (raw.replace(".", "").isdigit() and "." in raw):
        try:
            n = int(Decimal(raw))
        except Exception:
            return None
        # Serial Excel (planilhas)
        if 20000 < n < 80000:
            return (datetime(1899, 12, 30) + timedelta(days=n)).date()
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def find_column(fieldnames: list[str], *must_contain: str) -> str | None:
    must = [_norm(x) for x in must_contain]
    for c in fieldnames:
        cn = _norm(c)
        if all(m in cn for m in must):
            return c
    return None


def build_column_map(fieldnames: list[str]) -> dict[str, str]:
    cols = [f.strip() for f in fieldnames if f.strip()]
    out: dict[str, str] = {}

    def grab(key: str, *must: str) -> None:
        c = find_column(cols, *must)
        if c:
            out[key] = c

    grab("nome", "nome")
    grab("email", "email")
    ig = find_column(cols, "instagran") or find_column(cols, "instagram")
    if ig:
        out["instagram"] = ig
    grab("fase", "fase", "acad")
    grab("telefone", "telefone")
    grab("evento", "evento")
    grab("categoria", "categoria", "prof")
    grab("data_captacao", "data", "capta")
    grab("especialidade", "especialidade")
    return out


def load_lookups():
    categorias = list(CategoriaProfissional.objects.filter(ativo=True))
    eventos = list(Evento.objects.all())
    fases = list(FaseAcademica.objects.filter(ativo=True, tipo=FaseAcademica.TipoFase.SEMESTRE))

    cat_by = {_norm(c.nome): c for c in categorias}
    ev_by = {_norm(e.nome): e for e in eventos}
    fase_by = {_norm(f.nome): f for f in fases}

    espec_por_cat: dict[int, dict[str, Especialidade]] = {}
    for e in Especialidade.objects.filter(ativo=True).select_related("categoria_profissional"):
        cid = e.categoria_profissional_id
        espec_por_cat.setdefault(cid, {})[_norm(e.nome)] = e

    return cat_by, ev_by, fase_by, espec_por_cat


def resolve_name(name: str, by_norm: dict[str, object]) -> object | None:
    n = _norm(name)
    if not n:
        return None
    if n in by_norm:
        return by_norm[n]
    # pequena tolerância: igual sem um sufixo curto
    for k, obj in by_norm.items():
        if k.startswith(n) or n.startswith(k):
            return obj
    return None


def resolve_especialidade(
    nome_csv: str,
    categoria: CategoriaProfissional,
    espec_por_cat: dict[int, dict[str, Especialidade]],
) -> Especialidade | None:
    raw = (nome_csv or "").strip()
    if not raw:
        return None
    n = _norm(raw)
    bucket = espec_por_cat.get(categoria.id, {})
    if n in bucket:
        return bucket[n]
    for kn, obj in bucket.items():
        if n in kn or kn in n:
            return obj
    return None


def is_student_cat(cat: CategoriaProfissional) -> bool:
    return (cat.nome or "").strip().lower() in STUDENT_PROFESSIONAL_CATEGORY_NAMES


def row_to_lead(
    row: dict[str, str],
    colmap: dict[str, str],
    cat_by: dict,
    ev_by: dict,
    fase_by: dict,
    espec_por_cat: dict,
    assume_lgpd: bool,
    relax_student_especialidade: bool,
) -> tuple[LeadEvento | None, str | None]:
    def cell(key: str) -> str:
        c = colmap.get(key)
        if not c:
            return ""
        return (row.get(c) or "").strip()

    def hdr(key: str) -> str:
        return colmap.get(key) or key

    def err(col_key: str, motivo: str) -> tuple[None, str]:
        v = cell(col_key) if col_key in colmap else ""
        return None, f'coluna "{hdr(col_key)}" valor={v!r} -> {motivo}'

    nome = cell("nome")
    if not nome:
        return None, f'coluna "{hdr("nome")}" valor vazio -> nome e obrigatorio'

    categoria_nome = cell("categoria")
    categoria = resolve_name(categoria_nome, cat_by)
    if not categoria:
        return err(
            "categoria",
            f"nao encontrada no banco (nome normalizado \"{_norm(categoria_nome)}\"). "
            "Confira acentos e nome identico ao cadastro de categorias.",
        )

    evento_nome = cell("evento")
    evento = resolve_name(evento_nome, ev_by)
    if not evento:
        return err(
            "evento",
            f"não encontrado no banco (normalizado «{_norm(evento_nome)}»). Confira o nome do evento.",
        )

    data_raw = cell("data_captacao")
    dc = parse_data_captacao(data_raw)
    if not dc:
        return err(
            "data_captacao",
            "data invalida (use serial Excel tipo 45978, ou dd/mm/aaaa, ou aaaa-mm-dd)",
        )

    tel_raw = cell("telefone")
    tel = normalize_phone(tel_raw)
    if tel and (len(tel) != 11 or tel[2] != "9"):
        return err(
            "telefone",
            f"apos normalizar digitos={tel!r}: precisa 11 digitos (DDD + 9 + 8 digitos). Original={tel_raw!r}",
        )

    student = is_student_cat(categoria)
    fase_nome = cell("fase")
    fase = None
    if fase_nome:
        fase = resolve_name(fase_nome, fase_by)
        if not fase:
            return err(
                "fase",
                f"nao encontrada nas fases ativas tipo Semestre (normalizado \"{_norm(fase_nome)}\")",
            )
    if student and not fase:
        return err("fase", "obrigatoria para categoria de estudante (deixe vazio so se nao for estudante)")

    esp_nome_csv = cell("especialidade")
    especialidade = resolve_especialidade(esp_nome_csv, categoria, espec_por_cat) if esp_nome_csv else None
    if esp_nome_csv and not especialidade:
        return err(
            "especialidade",
            f"nao existe para a categoria \"{categoria.nome}\" (normalizado \"{_norm(esp_nome_csv)}\"). "
            "A especialidade tem que existir nessa categoria no cadastro.",
        )

    if student and especialidade and not especialidade_eh_nao_informada(especialidade):
        if relax_student_especialidade:
            ni = resolve_especialidade("Não informado", categoria, espec_por_cat)
            if not ni:
                return err(
                    "especialidade",
                    "cadastro sem linha \"Nao informado\" para esta categoria; rode o SQL 020 ou cadastre no sistema",
                )
            especialidade = ni
        else:
            return err(
                "especialidade",
                "para estudante so e permitido vazio ou \"Nao informado\". "
                "Rode sem --strict-student-especialidade para trocar automaticamente por \"Nao informado\".",
            )

    if not student:
        fase = None

    email_val = cell("email") or ""
    instagram_val = cell("instagram") or ""

    lead = LeadEvento(
        nome=nome[:180],
        email=email_val[:190] if email_val else None,
        telefone=tel or None,
        instagram=instagram_val[:500] if instagram_val else None,
        tipo_lead=tipo_lead_for_categoria(categoria),
        categoria_profissional=categoria,
        especialidade=especialidade,
        fase_academica=fase,
        evento=evento,
        colaborador_id=None,
        data_captacao=dc,
        status=LeadEvento.StatusLead.NOVO,
        nivel_interesse=LeadEvento.NivelInteresse.FRIO,
        score=0,
        aceite_lgpd=assume_lgpd,
        aceita_comunicacao="nenhum",
    )
    return lead, None


def open_csv(path: Path, encoding: str, delimiter: str):
    return path.open("r", encoding=encoding, newline="")


def sniff_dialect(sample: str, delimiter: str | None) -> str:
    if delimiter:
        return delimiter
    if sample.count(";") >= sample.count(",") and ";" in sample:
        return ";"
    return ","


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga de leads a partir de CSV.")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=None,
        help="Arquivo CSV (padrão: primeiro .csv em Carga_Leads/)",
    )
    parser.add_argument("--encoding", default="cp1252", help="Encoding do arquivo (padrão cp1252)")
    parser.add_argument("--delimiter", default=None, help="Forçar delimitador ; ou ,")
    parser.add_argument("--dry-run", action="store_true", help="Só valida, não grava")
    parser.add_argument(
        "--no-lgpd",
        action="store_true",
        help="Marca aceite_lgpd=False (padrão: True, como captura com consentimento)",
    )
    parser.add_argument(
        "--strict-student-especialidade",
        action="store_true",
        help="Igual ao formulário: estudante só com especialidade vazia ou «Não informado» (senão rejeita a linha)",
    )
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args()

    assume_lgpd = not args.no_lgpd

    carga_dir = BASE_DIR / "Carga_Leads"
    if args.input:
        csv_path = args.input if args.input.is_absolute() else BASE_DIR / args.input
    else:
        csvs = sorted(carga_dir.glob("*.csv")) if carga_dir.is_dir() else []
        if not csvs:
            print("Nenhum CSV em Carga_Leads/. Use -i caminho/arquivo.csv", file=sys.stderr)
            return 1
        csv_path = csvs[0]
        print(f"Usando arquivo: {csv_path.relative_to(BASE_DIR)}")

    if not csv_path.is_file():
        print(f"Arquivo não encontrado: {csv_path}", file=sys.stderr)
        return 1

    sample = csv_path.read_bytes()[:8000].decode(args.encoding, errors="replace")
    delim = sniff_dialect(sample, args.delimiter)

    cat_by, ev_by, fase_by, espec_por_cat = load_lookups()

    ok = 0
    errors: list[tuple[int, str, str]] = []
    to_create: list[LeadEvento] = []
    batch_start_line = 2

    with open_csv(csv_path, args.encoding, delim) as f:
        reader = csv.DictReader(f, delimiter=delim)
        if not reader.fieldnames:
            print("CSV sem cabeçalho.", file=sys.stderr)
            return 1
        colmap = build_column_map(list(reader.fieldnames))
        required = ["nome", "telefone", "evento", "categoria", "data_captacao"]
        missing = [k for k in required if k not in colmap]
        if missing:
            print(f"Colunas não detectadas: {missing}. Cabeçalhos: {reader.fieldnames}", file=sys.stderr)
            return 1

        for i, row in enumerate(reader, start=2):
            lead, err = row_to_lead(
                row,
                colmap,
                cat_by,
                ev_by,
                fase_by,
                espec_por_cat,
                assume_lgpd=assume_lgpd,
                relax_student_especialidade=not args.strict_student_especialidade,
            )
            if err:
                nome_col = colmap.get("nome")
                nome_preview = (row.get(nome_col, "") if nome_col else "")[:60]
                errors.append((i, nome_preview, err))
                continue
            assert lead is not None
            to_create.append(lead)
            if len(to_create) >= args.batch_size:
                if not args.dry_run:
                    try:
                        with transaction.atomic():
                            LeadEvento.objects.bulk_create(to_create)
                    except DatabaseError as exc:
                        print(
                            f"ERRO DO BANCO ao gravar lote (aprox. linhas CSV {batch_start_line}-{i}): {exc}",
                            file=sys.stderr,
                        )
                        raise
                ok += len(to_create)
                batch_start_line = i + 1
                to_create = []

    if to_create and not args.dry_run:
        try:
            with transaction.atomic():
                LeadEvento.objects.bulk_create(to_create)
        except DatabaseError as exc:
            print(
                f"ERRO DO BANCO ao gravar ultimo lote (aprox. linhas CSV {batch_start_line}-{batch_start_line + len(to_create) - 1}): {exc}",
                file=sys.stderr,
            )
            raise
    ok += len(to_create)

    def _console_safe(text: str) -> str:
        enc = getattr(sys.stdout, "encoding", None) or "cp1252"
        return text.encode(enc, errors="replace").decode(enc)

    print(_console_safe(f"Linhas gravadas: {ok}" if not args.dry_run else f"Linhas validas (dry-run): {ok}"))
    print(_console_safe(f"Linhas com erro: {len(errors)}"))

    err_path = None
    if errors:
        err_path = csv_path.with_name(csv_path.stem + "_erros_carga.tsv")
        with err_path.open("w", encoding="utf-8", newline="") as out:
            w = csv.writer(out, delimiter="\t")
            w.writerow(["linha_csv", "nome", "detalhe_erro"])
            for line_no, nome, err in errors:
                w.writerow([line_no, nome, err])
        print(_console_safe(f"Detalhe completo (UTF-8): {err_path.relative_to(BASE_DIR)}"))

    for line_no, nome, err in errors[:80]:
        line = f"  L{line_no} | {nome[:50]} | {err}"
        print(_console_safe(line))
    if len(errors) > 80:
        print(_console_safe(f"  ... e mais {len(errors) - 80} erros no arquivo TSV acima"))

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
