from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PREFILTER_COLUMNS = [
    "title",
    "company",
    "location",
    "url",
    "prefilter_score",
    "prefilter_reason",
    "should_keep",
    "should_enrich",
]


@dataclass(frozen=True)
class PrefilterAuditResult:
    input_path: Path
    markdown_path: Path
    csv_path: Path
    total: int
    kept: int
    discarded: int
    enrich: int
    buckets: dict[str, int]
    top_discard_reasons: list[tuple[str, int]]
    top_kept_companies: list[tuple[str, int]]
    top_discarded_companies: list[tuple[str, int]]
    top_locations: list[tuple[str, int]]


def find_latest_prefilter_csv(project_root: str | Path = ".") -> Path | None:
    debug_dir = Path(project_root) / "logs" / "gupy_debug"
    candidates = sorted(debug_dir.glob("prefilter_*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def load_prefilter_rows(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = []
        for row in reader:
            normalized = {column: str(row.get(column, "") or "") for column in PREFILTER_COLUMNS}
            normalized["prefilter_score"] = f"{_float_value(normalized['prefilter_score']):.1f}"
            normalized["should_keep"] = str(_bool_value(normalized["should_keep"]))
            normalized["should_enrich"] = str(_bool_value(normalized["should_enrich"]))
            normalized["audit_bucket"] = classify_audit_bucket(normalized)
            rows.append(normalized)
    return rows


def classify_audit_bucket(row: dict[str, str]) -> str:
    score = _float_value(row.get("prefilter_score", "0"))
    reason = (row.get("prefilter_reason") or "").casefold()
    should_keep = _bool_value(row.get("should_keep", "False"))

    if should_keep and score >= 50:
        return "kept_high_score"
    if not should_keep and score >= 30:
        return "discarded_high_score"
    if not should_keep and "negativo forte" in reason:
        return "discarded_strong_negative"
    if not should_keep and ("sem sinais tecnicos" in reason or "sem sinais técnicos" in reason):
        return "discarded_no_technical_term"
    if should_keep and score < 30:
        return "kept_low_score"
    return "ambiguous"


def generate_prefilter_audit(
    input_path: str | Path,
    reports_dir: str | Path = "reports",
) -> PrefilterAuditResult:
    source_path = Path(input_path)
    rows = load_prefilter_rows(source_path)
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_path = reports_path / f"prefilter_audit_{timestamp}.md"
    csv_path = reports_path / f"prefilter_audit_{timestamp}.csv"

    _write_audit_csv(rows, csv_path)
    markdown_path.write_text(_render_markdown(source_path, rows), encoding="utf-8")

    kept_rows = [row for row in rows if _bool_value(row["should_keep"])]
    discarded_rows = [row for row in rows if not _bool_value(row["should_keep"])]
    return PrefilterAuditResult(
        input_path=source_path,
        markdown_path=markdown_path,
        csv_path=csv_path,
        total=len(rows),
        kept=len(kept_rows),
        discarded=len(discarded_rows),
        enrich=sum(1 for row in rows if _bool_value(row["should_enrich"])),
        buckets=dict(Counter(row["audit_bucket"] for row in rows)),
        top_discard_reasons=_top_discard_reasons(discarded_rows),
        top_kept_companies=_counter_top(row["company"] for row in kept_rows),
        top_discarded_companies=_counter_top(row["company"] for row in discarded_rows),
        top_locations=_counter_top(row["location"] for row in rows),
    )


def _write_audit_csv(rows: list[dict[str, str]], path: Path) -> None:
    fieldnames = PREFILTER_COLUMNS + ["audit_bucket"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _render_markdown(input_path: Path, rows: list[dict[str, str]]) -> str:
    kept = [row for row in rows if _bool_value(row["should_keep"])]
    discarded = [row for row in rows if not _bool_value(row["should_keep"])]
    enrich = [row for row in rows if _bool_value(row["should_enrich"])]
    buckets = Counter(row["audit_bucket"] for row in rows)

    lines = [
        "# Auditoria do Pre-filtro",
        "",
        "## Resumo executivo",
        "",
        f"- Arquivo analisado: `{input_path}`",
        f"- Total auditado: {len(rows)}",
        f"- Mantidas: {len(kept)}",
        f"- Descartadas: {len(discarded)}",
        f"- Selecionadas para enriquecimento: {len(enrich)}",
        f"- Principal bucket: {_top_one(buckets)}",
        "",
        "## Totais",
        "",
        "| Metrica | Valor |",
        "| --- | ---: |",
        f"| Total | {len(rows)} |",
        f"| Mantidas | {len(kept)} |",
        f"| Descartadas | {len(discarded)} |",
        f"| Enriquecimento | {len(enrich)} |",
        "",
    ]
    lines.extend(_table_section("Vagas mantidas com maior score", _sort_rows(kept, reverse=True)[:10]))
    lines.extend(_table_section("Vagas mantidas com menor score", _sort_rows(kept, reverse=False)[:10]))
    lines.extend(_table_section("Vagas descartadas com maior score", _sort_rows(discarded, reverse=True)[:10]))
    lines.extend(
        _table_section(
            "Vagas descartadas por negativo forte",
            [row for row in discarded if "negativo forte" in row["prefilter_reason"].casefold()][:10],
        )
    )
    lines.extend(
        _table_section(
            "Vagas descartadas por falta de termo tecnico",
            [row for row in discarded if row["audit_bucket"] == "discarded_no_technical_term"][:10],
        )
    )
    lines.extend(_table_section("Vagas ambiguas", [row for row in rows if row["audit_bucket"] == "ambiguous"][:10]))
    lines.extend(_counter_section("Principais motivos de descarte", _top_discard_reasons(discarded)))
    lines.extend(_counter_section("Empresas mais frequentes", _counter_top(row["company"] for row in rows)))
    lines.extend(_counter_section("Empresas com vagas mantidas", _counter_top(row["company"] for row in kept)))
    lines.extend(_counter_section("Empresas com vagas descartadas", _counter_top(row["company"] for row in discarded)))
    lines.extend(_counter_section("Localidades mais frequentes", _counter_top(row["location"] for row in rows)))
    lines.extend(
        [
            "## Recomendacoes de ajuste",
            "",
            "- Revisar `discarded_high_score` para encontrar possiveis falsos negativos.",
            "- Revisar `kept_low_score` para decidir se o limite de manutencao deve subir.",
            "- Se houver boas vagas em `discarded_no_technical_term`, adicionar termos em `technical_title_keywords` ou `technical_area_keywords`.",
            "- Se houver vagas ruins mantidas, adicionar termos em `strong_negative_title_keywords` ou `weak_negative_title_keywords`.",
            "- Empresas com muitos descartes podem precisar de menor prioridade ou filtros especificos.",
            "",
        ]
    )
    return "\n".join(lines)


def _table_section(title: str, rows: list[dict[str, str]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not rows:
        return lines + ["Nenhuma vaga nesta categoria.", ""]
    lines.extend(["| Score | Titulo | Empresa | Local | Bucket |", "| ---: | --- | --- | --- | --- |"])
    for row in rows:
        lines.append(
            f"| {row['prefilter_score']} | {_escape_md(row['title'])} | {_escape_md(row['company'])} | "
            f"{_escape_md(row['location'])} | {row['audit_bucket']} |"
        )
    lines.append("")
    return lines


def _counter_section(title: str, items: list[tuple[str, int]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        return lines + ["Nenhum dado encontrado.", ""]
    lines.extend(["| Item | Total |", "| --- | ---: |"])
    for item, count in items[:15]:
        lines.append(f"| {_escape_md(item)} | {count} |")
    lines.append("")
    return lines


def _top_discard_reasons(rows: list[dict[str, str]]) -> list[tuple[str, int]]:
    return _counter_top(_reason_key(row["prefilter_reason"]) for row in rows)


def _reason_key(reason: str) -> str:
    reason = reason or "sem motivo"
    if "negativo forte" in reason.casefold():
        return "negativo forte"
    if "sem sinais tecnicos" in reason.casefold() or "sem sinais técnicos" in reason.casefold():
        return "sem sinais tecnicos"
    if "negativo fraco" in reason.casefold():
        return "negativo fraco"
    return reason.split(":", 1)[0].strip() or "outros"


def _counter_top(values) -> list[tuple[str, int]]:
    cleaned = [str(value).strip() or "Nao informado" for value in values]
    return Counter(cleaned).most_common(15)


def _sort_rows(rows: list[dict[str, str]], reverse: bool) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: _float_value(row["prefilter_score"]), reverse=reverse)


def _top_one(counter: Counter) -> str:
    if not counter:
        return "sem dados"
    key, value = counter.most_common(1)[0]
    return f"{key} ({value})"


def _bool_value(value: object) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes", "sim"}


def _float_value(value: object) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def _escape_md(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()
