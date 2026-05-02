"""Gera varios arquivos 017_cidades_part_XX.sql (um INSERT por arquivo) a partir do IBGE."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.request import urlopen

MUNICIPIOS_URL = "https://raw.githubusercontent.com/chandez/Estados-Cidades-IBGE/master/sql/Municipios.sql"
OUT_DIR = Path(__file__).resolve().parent.parent / "Codigos SQL"
PREFIX = "017_cidades_part_"
BATCH = 400


def parse_line(line: str) -> tuple[int, int, str] | None:
    line = line.strip()
    if not line.lower().startswith("insert into municipio"):
        return None
    m = re.search(
        r"values\s*\(\s*'(\d+)'\s*,\s*((?:'(?:[^']|'')*'))\s*,\s*'([A-Z]{2})'\s*\)\s*;",
        line,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    codigo, nome_quoted, _uf = m.groups()
    cid = int(codigo)
    inner = nome_quoted[1:-1]
    nome = inner.replace("''", "'")
    estado_id = cid // 100_000
    return cid, estado_id, nome


def sql_escape(s: str) -> str:
    return s.replace("'", "''")


def main() -> None:
    text = urlopen(MUNICIPIOS_URL).read().decode("utf-8")
    rows: list[tuple[int, int, str]] = []
    for line in text.splitlines():
        parsed = parse_line(line)
        if parsed:
            rows.append(parsed)
    if len(rows) < 5000:
        print(f"Esperado ~5570 municipios, encontrados {len(rows)}", file=sys.stderr)
        sys.exit(1)

    for old in OUT_DIR.glob(f"{PREFIX}*.sql"):
        old.unlink()

    part = 0
    for i in range(0, len(rows), BATCH):
        part += 1
        chunk = rows[i : i + BATCH]
        values = ",\n  ".join(f"({cid}, {eid}, '{sql_escape(nome)}')" for cid, eid, nome in chunk)
        body = (
            f"-- Parte {part} — um comando por execucao no DBeaver\n"
            f"-- Fonte: https://github.com/chandez/Estados-Cidades-IBGE\n\n"
            f"INSERT INTO db_concimed.concimed_cidade (id, estado_id, nome) VALUES\n  {values};\n"
        )
        path = OUT_DIR / f"{PREFIX}{part:02d}.sql"
        path.write_text(body, encoding="utf-8")

    legacy = OUT_DIR / "017_seed_concimed_cidades.sql"
    if legacy.exists():
        legacy.unlink()

    print(f"Escritos {part} arquivos em {OUT_DIR} ({PREFIX}01.sql … {PREFIX}{part:02d}.sql), {len(rows)} municipios.")


if __name__ == "__main__":
    main()
