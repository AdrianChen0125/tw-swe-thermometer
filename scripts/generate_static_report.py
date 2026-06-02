#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


SITE_TITLE = "Taiwan 軟體開發者航行指南"
SITE_EYEBROW = "Taiwan Software Developer Navigation Guide"
NAV_ITEMS = [
    ("index.html", "總覽"),
    ("industry.html", "產業"),
    ("role.html", "職能"),
    ("experience.html", "年資"),
    ("company.html", "SaaS案例"),
    ("cross_analysis.html", "交叉分析"),
    ("high_salary.html", "高薪樣本"),
    ("actions.html", "行動建議"),
]
MAIN_CHART_MIN_SAMPLES = 10
CROSS_ANALYSIS_MIN_SAMPLES = 5
COMPANY_SOURCE_NAME = "91APP"
COMPANY_DISPLAY_NAME = "SaaS 公司案例"
COMPANY_CATEGORY_NAME = "software_internet"
COMPANY_PAGE_HREF = "company.html"
INDUSTRY_LABELS = {
    "software_internet": "軟體 / 網路",
    "semiconductor_electronics": "半導體 / 電子",
    "it_services": "IT 服務",
    "financial": "金融 / FinTech",
    "cybersecurity": "資安",
    "startup": "新創",
    "gaming_entertainment": "遊戲 / 娛樂",
    "ecommerce_retail": "電商 / 零售",
    "telecom": "電信",
    "blockchain_crypto": "區塊鏈 / 加密貨幣",
    "gambling": "博弈",
    "manufacturing_industrial": "製造 / 工業",
    "healthcare_biotech": "醫療 / 生技",
    "transport_logistics": "交通 / 物流平台",
    "media_publishing": "媒體 / 出版",
    "government_research": "政府 / 研究",
    "travel_tourism": "旅遊",
    "edtech": "教育科技",
    "delivery_platform": "外送 / 平台",
}


def parse_number(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0
    values = sorted(values)
    position = (len(values) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[int(position)]
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def fmt(value: float, digits: int = 1) -> str:
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def load_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def numeric_values(rows: list[dict[str, str]], key: str) -> list[float]:
    values = []
    for row in rows:
        value = parse_number(row.get(key, ""))
        if value is not None:
            values.append(value)
    return values


def bucket_experience(value: float | None) -> str:
    if value is None:
        return "未知"
    if value < 1:
        return "0-1 年"
    if value < 3:
        return "1-3 年"
    if value < 5:
        return "3-5 年"
    if value < 8:
        return "5-8 年"
    return "8+ 年"


def group_rows(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row[key]].append(row)
    return dict(groups)


def salary_stats(rows: list[dict[str, str]]) -> dict[str, float]:
    monthly = numeric_values(rows, "monthly_wage")
    total = numeric_values(rows, "total")
    bonus = numeric_values(rows, "bonus")
    return {
        "count": len(rows),
        "monthly_median": statistics.median(monthly) if monthly else 0,
        "monthly_p25": percentile(monthly, 0.25),
        "monthly_p75": percentile(monthly, 0.75),
        "total_median": statistics.median(total) if total else 0,
        "total_p25": percentile(total, 0.25),
        "total_p75": percentile(total, 0.75),
        "bonus_median": statistics.median(bonus) if bonus else 0,
    }


def industry_label(value: str) -> str:
    return INDUSTRY_LABELS.get(value, value)


def relabel_first_column(rows: list[list[str]], labels: dict[str, str]) -> list[list[str]]:
    return [[labels.get(row[0], row[0]), *row[1:]] for row in rows]


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def ensure_dirs(output_dir: Path) -> tuple[Path, Path]:
    assets_dir = output_dir / "assets"
    charts_dir = assets_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir, charts_dir


def write_svg(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def bar_chart(path: Path, title: str, items: list[tuple[str, float]], unit: str) -> None:
    items = items[:12]
    width = 960
    row_height = 38
    top = 74
    left = 230
    height = top + row_height * len(items) + 34
    max_value = max((value for _, value in items), default=1)
    rows = []
    for index, (label, value) in enumerate(items):
        y = top + index * row_height
        bar_width = 620 * (value / max_value) if max_value else 0
        rows.append(
            f'<text x="24" y="{y + 22}" class="label">{html.escape(label)}</text>'
            f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="24" rx="4" class="bar"/>'
            f'<text x="{left + bar_width + 12:.1f}" y="{y + 18}" class="value">{html.escape(fmt(value))} {unit}</text>'
        )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
<style>
.title{{font:700 28px sans-serif;fill:#0f172a}}.label{{font:16px sans-serif;fill:#334155}}.value{{font:16px sans-serif;fill:#0f172a}}.bar{{fill:#2563eb}}
</style>
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="24" y="38" class="title">{html.escape(title)}</text>
{''.join(rows)}
</svg>
"""
    write_svg(path, svg)


def histogram(path: Path, title: str, values: list[float], unit: str, bins: int = 12) -> None:
    width, height = 960, 420
    left, right, top, bottom = 64, 28, 70, 58
    if not values:
        write_svg(path, f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"></svg>')
        return
    min_v, max_v = min(values), max(values)
    if min_v == max_v:
        max_v = min_v + 1
    step = (max_v - min_v) / bins
    counts = [0] * bins
    for value in values:
        index = min(int((value - min_v) / step), bins - 1)
        counts[index] += 1
    max_count = max(counts) or 1
    plot_w = width - left - right
    plot_h = height - top - bottom
    bar_gap = 7
    bar_w = plot_w / bins - bar_gap
    bars = []
    labels = []
    for index, count in enumerate(counts):
        bar_h = plot_h * count / max_count
        x = left + index * (plot_w / bins) + bar_gap / 2
        y = top + plot_h - bar_h
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="4" class="bar"/>')
        if index % 2 == 0:
            label = min_v + step * index
            labels.append(f'<text x="{x:.1f}" y="{height - 24}" class="axis">{html.escape(fmt(label))}</text>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
<style>
.title{{font:700 28px sans-serif;fill:#0f172a}}.axis{{font:15px sans-serif;fill:#475569}}.bar{{fill:#14b8a6}}.note{{font:15px sans-serif;fill:#475569}}
</style>
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="24" y="38" class="title">{html.escape(title)}</text>
<text x="{left}" y="{height - 8}" class="note">單位：{html.escape(unit)}</text>
<line x1="{left}" y1="{top + plot_h}" x2="{width - right}" y2="{top + plot_h}" stroke="#cbd5e1"/>
{''.join(bars)}
{''.join(labels)}
</svg>
"""
    write_svg(path, svg)


def line_chart(
    path: Path,
    title: str,
    items: list[tuple[str, float]],
    unit: str,
    comparison: list[tuple[str, float]] | None = None,
    comparison_label: str = "預期值",
) -> None:
    width, height = 960, 420
    left, right, top, bottom = 74, 36, 72, 68
    plot_w = width - left - right
    plot_h = height - top - bottom
    all_values = [value for _, value in items]
    if comparison:
        all_values.extend(value for _, value in comparison)
    max_value = max(all_values, default=1)
    points = []
    labels = []
    for index, (label, value) in enumerate(items):
        x = left + (plot_w * index / max(len(items) - 1, 1))
        y = top + plot_h - (plot_h * value / max_value)
        points.append((x, y))
        labels.append(f'<text x="{x:.1f}" y="{height - 28}" text-anchor="middle" class="axis">{html.escape(label)}</text>')
    path_data = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(points))
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" class="dot"/>' for x, y in points)
    values = "".join(
        f'<text x="{x:.1f}" y="{min(top + plot_h - 10, y + 28):.1f}" text-anchor="middle" class="value">{html.escape(fmt(items[i][1]))}</text>'
        for i, (x, y) in enumerate(points)
    )
    comparison_path = ""
    comparison_dots = ""
    comparison_values = ""
    comparison_legend = ""
    if comparison:
        comparison_points = []
        for index, (_, value) in enumerate(comparison):
            x = left + (plot_w * index / max(len(comparison) - 1, 1))
            y = top + plot_h - (plot_h * value / max_value)
            comparison_points.append((x, y))
        comparison_path_data = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(comparison_points))
        comparison_path = f'<path d="{comparison_path_data}" class="comparison-line"/>'
        comparison_dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="comparison-dot"/>' for x, y in comparison_points)
        comparison_labels = []
        for i, (x, y) in enumerate(comparison_points):
            actual_y = points[i][1] if i < len(points) else y
            label_y = max(top + 18, y - 18)
            if abs(label_y - (actual_y + 28)) < 24:
                label_y = max(top + 18, y - 34)
            comparison_labels.append(
                f'<text x="{x:.1f}" y="{label_y:.1f}" text-anchor="middle" class="comparison-value">{html.escape(fmt(comparison[i][1]))}</text>'
            )
        comparison_values = "".join(comparison_labels)
        comparison_legend = (
            f'<g><rect x="{width - right - 178}" y="26" width="12" height="12" rx="3" fill="#f97316"/>'
            f'<text x="{width - right - 158}" y="36" class="legend">實際中位數</text></g>'
            f'<g><rect x="{width - right - 178}" y="50" width="12" height="12" rx="3" fill="#2563eb"/>'
            f'<text x="{width - right - 158}" y="60" class="legend">{html.escape(comparison_label)}</text></g>'
        )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
<style>
.title{{font:700 28px sans-serif;fill:#0f172a}}.axis{{font:15px sans-serif;fill:#475569}}.value{{font:16px sans-serif;fill:#0f172a}}.comparison-value{{font:15px sans-serif;fill:#2563eb}}.legend{{font:15px sans-serif;fill:#334155}}.line{{fill:none;stroke:#f97316;stroke-width:4}}.dot{{fill:#f97316}}.comparison-line{{fill:none;stroke:#2563eb;stroke-width:3;stroke-dasharray:8 6}}.comparison-dot{{fill:#2563eb}}
</style>
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="24" y="38" class="title">{html.escape(title)}（{html.escape(unit)}）</text>
<line x1="{left}" y1="{top + plot_h}" x2="{width - right}" y2="{top + plot_h}" stroke="#cbd5e1"/>
<path d="{path_data}" class="line"/>
{comparison_path}
{dots}
{comparison_dots}
{values}
{comparison_values}
{''.join(labels)}
{comparison_legend}
</svg>
"""
    write_svg(path, svg)


def multi_line_chart(path: Path, title: str, labels: list[str], series: list[tuple[str, list[float | None]]], unit: str) -> None:
    width, height = 960, 440
    left, right, top, bottom = 76, 42, 76, 72
    plot_w = width - left - right
    plot_h = height - top - bottom
    values = [value for _, points in series for value in points if value is not None]
    max_value = max(values, default=1)
    colors = ["#2563eb", "#f97316", "#14b8a6", "#e11d48"]
    x_positions = [left + (plot_w * index / max(len(labels) - 1, 1)) for index in range(len(labels))]

    paths = []
    legend = []
    points = []
    for series_index, (name, values) in enumerate(series):
        color = colors[series_index % len(colors)]
        segments = []
        current = []
        for index, value in enumerate(values):
            if value is None:
                if current:
                    segments.append(current)
                    current = []
                continue
            x = x_positions[index]
            y = top + plot_h - (plot_h * value / max_value)
            current.append((x, y))
            points.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{color}" stroke="#ffffff" stroke-width="2"/>')
        if current:
            segments.append(current)
        for segment in segments:
            path_data = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(segment))
            paths.append(f'<path d="{path_data}" class="series" stroke="{color}"/>')
        legend.append(
            f'<g><rect x="{width - right - 168}" y="{26 + series_index * 24}" width="12" height="12" rx="3" fill="{color}"/>'
            f'<text x="{width - right - 148}" y="{36 + series_index * 24}" class="legend">{html.escape(name)}</text></g>'
        )

    x_labels = [
        f'<text x="{x:.1f}" y="{height - 28}" text-anchor="middle" class="axis">{html.escape(label)}</text>'
        for x, label in zip(x_positions, labels)
    ]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
<style>
.title{{font:700 28px sans-serif;fill:#0f172a}}.axis{{font:15px sans-serif;fill:#475569}}.legend{{font:15px sans-serif;fill:#334155}}.series{{fill:none;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}}
</style>
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="24" y="38" class="title">{html.escape(title)}（{html.escape(unit)}）</text>
<line x1="{left}" y1="{top + plot_h}" x2="{width - right}" y2="{top + plot_h}" stroke="#cbd5e1"/>
{''.join(paths)}
{''.join(points)}
{''.join(x_labels)}
{''.join(legend)}
</svg>
"""
    write_svg(path, svg)


def grouped_bar_chart(path: Path, title: str, labels: list[str], series: list[tuple[str, list[float | None]]], unit: str) -> None:
    width, height = 960, 460
    left, right, top, bottom = 74, 42, 82, 82
    plot_w = width - left - right
    plot_h = height - top - bottom
    values = [value for _, points in series for value in points if value is not None]
    max_value = max(values, default=1)
    colors = ["#2563eb", "#f97316", "#14b8a6", "#e11d48"]
    group_w = plot_w / max(len(labels), 1)
    bar_gap = 5
    bar_w = min(34, (group_w - 22) / max(len(series), 1) - bar_gap)

    bars = []
    value_labels = []
    legend = []
    for series_index, (name, points) in enumerate(series):
        color = colors[series_index % len(colors)]
        legend.append(
            f'<g><rect x="{width - right - 168}" y="{26 + series_index * 24}" width="12" height="12" rx="3" fill="{color}"/>'
            f'<text x="{width - right - 148}" y="{36 + series_index * 24}" class="legend">{html.escape(name)}</text></g>'
        )
        for label_index, value in enumerate(points):
            if value is None:
                continue
            group_x = left + label_index * group_w
            x = group_x + (group_w - (bar_w + bar_gap) * len(series)) / 2 + series_index * (bar_w + bar_gap)
            bar_h = plot_h * value / max_value if max_value else 0
            y = top + plot_h - bar_h
            bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="4" fill="{color}"/>')
            value_labels.append(
                f'<text x="{x + bar_w / 2:.1f}" y="{y - 7:.1f}" text-anchor="middle" class="value">{html.escape(fmt(value))}</text>'
            )

    x_labels = [
        f'<text x="{left + index * group_w + group_w / 2:.1f}" y="{height - 34}" text-anchor="middle" class="axis">{html.escape(label)}</text>'
        for index, label in enumerate(labels)
    ]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
<style>
.title{{font:700 28px sans-serif;fill:#0f172a}}.axis{{font:15px sans-serif;fill:#475569}}.legend{{font:15px sans-serif;fill:#334155}}.value{{font:15px sans-serif;fill:#0f172a}}
</style>
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="24" y="38" class="title">{html.escape(title)}（{html.escape(unit)}）</text>
<line x1="{left}" y1="{top + plot_h}" x2="{width - right}" y2="{top + plot_h}" stroke="#cbd5e1"/>
{''.join(bars)}
{''.join(value_labels)}
{''.join(x_labels)}
{''.join(legend)}
</svg>
"""
    write_svg(path, svg)


def page(title: str, active_href: str, body: str) -> str:
    nav = "".join(
        f'<a class="{"active" if href == active_href else ""}" href="{href}">{label}</a>'
        for href, label in NAV_ITEMS
    )
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} | {SITE_TITLE}</title>
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
  <header class="site-header">
    <div>
      <p class="eyebrow">{html.escape(SITE_EYEBROW)}</p>
      <h1>{html.escape(title)}</h1>
    </div>
    <nav>{nav}</nav>
  </header>
  <main>{body}</main>
  <footer>資料為匿名薪資樣本彙整，頁面僅呈現彙總統計。</footer>
</body>
</html>
"""


def stat_cards(stats: dict[str, float]) -> str:
    cards = [
        ("樣本數", f"{int(stats['count'])}"),
        ("月薪中位數", f"{fmt(stats['monthly_median'])} 萬"),
        ("年薪中位數", f"{fmt(stats['total_median'])} 萬"),
        ("Bonus 中位數", f"{fmt(stats['bonus_median'])} 個月"),
    ]
    return '<section class="metric-grid">' + "".join(
        f'<div class="metric"><span>{label}</span><strong>{value}</strong></div>'
        for label, value in cards
    ) + "</section>"


def insight_box(title: str, items: list[str]) -> str:
    bullets = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    return f"""
<section class="insight">
  <h2>{html.escape(title)}</h2>
  <ul>{bullets}</ul>
</section>
"""


def chart_note(text: str) -> str:
    return f'<p class="chart-note">{html.escape(text)}</p>'


def grouped_table(groups: dict[str, list[dict[str, str]]]) -> list[list[str]]:
    rows = []
    for label, items in groups.items():
        stats = salary_stats(items)
        count = int(stats["count"])
        rows.append([
            label,
            str(count),
            fmt(stats["monthly_median"]),
            f"{fmt(stats['monthly_p25'])} - {fmt(stats['monthly_p75'])}",
            fmt(stats["total_median"]),
            f"{fmt(stats['total_p25'])} - {fmt(stats['total_p75'])}",
        ])
    return sorted(rows, key=lambda row: (float(row[4]), int(row[1])), reverse=True)


def enough_samples(row: list[str]) -> bool:
    return int(row[1]) >= MAIN_CHART_MIN_SAMPLES


def split_sample_rows(rows: list[list[str]]) -> tuple[list[list[str]], list[list[str]]]:
    stable = [row for row in rows if enough_samples(row)]
    small = [row for row in rows if not enough_samples(row)]
    return stable, small


def order_rows(rows: list[list[str]], labels: list[str]) -> list[list[str]]:
    positions = {label: index for index, label in enumerate(labels)}
    return sorted(rows, key=lambda row: positions.get(row[0], len(positions)))


def experience_bucket_order() -> list[str]:
    return ["0-1 年", "1-3 年", "3-5 年", "5-8 年", "8+ 年"]

def summarize_by_bucket(rows: list[dict[str, str]], bucket_order: list[str]) -> dict[str, dict[str, float | int]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        bucket = bucket_experience(parse_number(row["year_of_experience"]))
        if bucket == "未知":
            continue
        groups[bucket].append(row)
    summary: dict[str, dict[str, float | int]] = {}
    for bucket in bucket_order:
        items = groups.get(bucket, [])
        monthly = numeric_values(items, "monthly_wage")
        total = numeric_values(items, "total")
        summary[bucket] = {
            "count": len(items),
            "monthly": statistics.median(monthly) if monthly else 0,
            "total": statistics.median(total) if total else 0,
        }
    return summary


def bucket_label_from_row(row: dict[str, str]) -> str:
    return bucket_experience(parse_number(row["year_of_experience"]))


def median_total(rows: list[dict[str, str]]) -> float:
    values = numeric_values(rows, "total")
    return statistics.median(values) if values else 0


def linear_regression(points: list[tuple[float, float]]) -> dict[str, float]:
    count = len(points)
    if count < 2:
        return {"count": count, "intercept": 0, "slope": 0, "r2": 0}
    mean_x = sum(x for x, _ in points) / count
    mean_y = sum(y for _, y in points) / count
    sxx = sum((x - mean_x) ** 2 for x, _ in points)
    if not sxx:
        return {"count": count, "intercept": mean_y, "slope": 0, "r2": 0}
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in points)
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    sst = sum((y - mean_y) ** 2 for _, y in points)
    sse = sum((y - (intercept + slope * x)) ** 2 for x, y in points)
    r2 = 1 - sse / sst if sst else 0
    return {"count": count, "intercept": intercept, "slope": slope, "r2": r2}


def cohort_gap_table(
    rows: list[dict[str, str]],
    key: str,
    min_samples: int = CROSS_ANALYSIS_MIN_SAMPLES,
) -> list[list[str]]:
    groups: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: {"early": [], "senior": []})
    for row in rows:
        bucket = bucket_label_from_row(row)
        if bucket in {"0-1 年", "1-3 年", "3-5 年"}:
            groups[row[key]]["early"].append(row)
        elif bucket in {"5-8 年", "8+ 年"}:
            groups[row[key]]["senior"].append(row)

    result = []
    for label, cohorts in groups.items():
        early = cohorts["early"]
        senior = cohorts["senior"]
        if len(early) < min_samples or len(senior) < min_samples:
            continue
        early_median = median_total(early)
        senior_median = median_total(senior)
        result.append([
            label,
            str(len(early)),
            fmt(early_median),
            str(len(senior)),
            fmt(senior_median),
            fmt(senior_median - early_median),
            fmt(senior_median / early_median, 2) if early_median else "",
        ])
    return sorted(result, key=lambda row: float(row[5]), reverse=True)


def write_styles(path: Path) -> None:
    path.write_text(""":root {
  color-scheme: light;
  --ink: #0f172a;
  --muted: #475569;
  --line: rgba(15, 23, 42, .12);
  --paper: #f7f8fc;
  --panel: #ffffff;
  --accent: #14b8a6;
  --accent-2: #f97316;
  --accent-3: #2563eb;
  --accent-4: #e11d48;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  position: relative;
  overflow-x: hidden;
  background:
    radial-gradient(circle at top left, rgba(20, 184, 166, .16), transparent 30%),
    radial-gradient(circle at top right, rgba(249, 115, 22, .16), transparent 28%),
    radial-gradient(circle at 85% 68%, rgba(225, 29, 72, .12), transparent 24%),
    linear-gradient(180deg, #f9fbff 0%, #eef2ff 48%, #f8fafc 100%);
  color: var(--ink);
  font-family: Inter, "Avenir Next", "Segoe UI", "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif;
  line-height: 1.55;
}
.site-header {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 28px;
  align-items: end;
  padding: 38px clamp(20px, 5vw, 72px) 24px;
  color: white;
  background:
    radial-gradient(circle at top right, rgba(249, 115, 22, .32), transparent 24%),
    linear-gradient(135deg, #0f172a 0%, #1e3a8a 58%, #0f766e 100%);
  box-shadow: 0 24px 60px rgba(15, 23, 42, .18);
  border-bottom: 1px solid rgba(255, 255, 255, .12);
}
.eyebrow {
  margin: 0 0 8px;
  color: #fbbf24;
  font: 700 12px/1.2 ui-sans-serif, system-ui, sans-serif;
  letter-spacing: .08em;
  text-transform: uppercase;
}
h1 {
  max-width: 900px;
  margin: 0;
  font-size: clamp(34px, 6vw, 72px);
  line-height: .92;
  letter-spacing: 0;
}
h2 {
  margin: 0 0 16px;
  font-size: clamp(24px, 3vw, 36px);
  line-height: 1.05;
  letter-spacing: 0;
}
nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  font-family: ui-sans-serif, system-ui, sans-serif;
}
nav a {
  color: rgba(255,255,255,.92);
  border: 1px solid rgba(255,255,255,.18);
  border-radius: 999px;
  padding: 8px 12px;
  text-decoration: none;
  background: rgba(255,255,255,.10);
  backdrop-filter: blur(8px);
  box-shadow: 0 8px 24px rgba(15, 23, 42, .12);
  transition: transform .18s ease, box-shadow .18s ease, background .18s ease;
}
nav a:hover {
  transform: translateY(-1px);
  background: rgba(255,255,255,.16);
  box-shadow: 0 12px 28px rgba(15, 23, 42, .18);
}
nav a.active {
  color: white;
  border-color: transparent;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
}
main {
  width: min(1120px, calc(100% - 40px));
  margin: 0 auto;
  padding: 36px 0 72px;
}
section {
  margin: 0 0 32px;
}
.lede {
  max-width: 780px;
  color: #334155;
  font-size: 20px;
}
.chart-note {
  margin: 10px 0 0;
  color: #475569;
  font: 14px/1.45 ui-sans-serif, system-ui, sans-serif;
}
.insight {
  padding: 18px 20px;
  border: 1px solid rgba(20, 184, 166, .18);
  border-left: 5px solid var(--accent);
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f7fffd 100%);
  box-shadow: 0 18px 40px rgba(15, 23, 42, .08);
}
.insight h2 {
  margin: 0 0 10px;
  font-size: 22px;
}
.insight ul {
  margin: 0;
  padding-left: 20px;
  color: #334155;
  font-size: 17px;
}
.insight li + li {
  margin-top: 6px;
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}
.metric {
  border: 1px solid rgba(15, 23, 42, .08);
  border-radius: 18px;
  padding: 18px;
  background: linear-gradient(180deg, rgba(255,255,255,.98) 0%, rgba(248,250,252,.95) 100%);
  box-shadow: 0 18px 40px rgba(15, 23, 42, .08);
  position: relative;
  overflow: hidden;
}
.metric::before {
  content: "";
  position: absolute;
  inset: 0 auto auto 0;
  width: 100%;
  height: 6px;
  background: linear-gradient(90deg, var(--accent) 0%, var(--accent-2) 55%, var(--accent-4) 100%);
}
.metric span {
  display: block;
  color: var(--muted);
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-size: 13px;
}
.metric strong {
  display: block;
  margin-top: 8px;
  font-size: 32px;
  line-height: 1;
}
.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}
.chart {
  margin: 0;
  border: 1px solid rgba(15, 23, 42, .08);
  border-radius: 18px;
  padding: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 18px 42px rgba(15, 23, 42, .08);
}
.chart img {
  display: block;
  width: 100%;
  height: auto;
}
.table-scroll {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  overflow: hidden;
  border-radius: 18px;
  background: white;
  font-family: ui-sans-serif, system-ui, sans-serif;
  box-shadow: 0 18px 42px rgba(15, 23, 42, .08);
}
th, td {
  padding: 11px 12px;
  border-bottom: 1px solid var(--line);
  text-align: right;
}
th:first-child, td:first-child { text-align: left; }
th {
  color: #0f172a;
  font-size: 13px;
  background: linear-gradient(180deg, #e0f2fe 0%, #ecfeff 100%);
}
footer {
  padding: 24px clamp(20px, 5vw, 72px);
  color: var(--muted);
  border-top: 1px solid var(--line);
  font-family: ui-sans-serif, system-ui, sans-serif;
}
@media (max-width: 820px) {
  body {
    line-height: 1.45;
    background: #f8fafc;
  }
  .site-header {
    grid-template-columns: 1fr;
    align-items: start;
    gap: 18px;
    padding: 24px 16px 16px;
  }
  .eyebrow {
    display: none;
  }
  h1 {
    font-size: 32px;
    line-height: 1.08;
  }
  h2 {
    margin-bottom: 10px;
    font-size: 22px;
    line-height: 1.15;
  }
  nav {
    flex-wrap: nowrap;
    justify-content: flex-start;
    gap: 6px;
    width: 100%;
    overflow-x: auto;
    padding-bottom: 2px;
    -webkit-overflow-scrolling: touch;
  }
  nav a {
    flex: 0 0 auto;
    padding: 7px 10px;
    font-size: 13px;
    white-space: nowrap;
    box-shadow: none;
  }
  main {
    width: min(100% - 24px, 1120px);
    padding: 22px 0 44px;
  }
  section {
    margin-bottom: 20px;
  }
  .lede {
    display: -webkit-box;
    max-width: none;
    margin: 0;
    overflow: hidden;
    color: #334155;
    font-size: 16px;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
  }
  .chart-note {
    display: none;
  }
  .insight {
    padding: 14px 14px;
    border-radius: 12px;
    box-shadow: none;
  }
  .insight h2 {
    font-size: 18px;
  }
  .insight ul {
    padding-left: 18px;
    font-size: 15px;
  }
  .insight li {
    display: none;
  }
  .insight li:first-child {
    display: list-item;
  }
  .metric-grid, .chart-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .metric {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    padding: 14px;
    border-radius: 12px;
    box-shadow: none;
  }
  .metric strong {
    margin-top: 0;
    font-size: 24px;
  }
  .chart {
    padding: 8px;
    border-radius: 12px;
    box-shadow: none;
  }
  .table-scroll,
  section:has(> table) {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  table {
    min-width: 640px;
    border-radius: 12px;
    font-size: 13px;
    box-shadow: none;
  }
  th, td {
    padding: 8px 9px;
    white-space: nowrap;
  }
  footer {
    padding: 18px 16px;
    font-size: 13px;
  }
}
""", encoding="utf-8")


def build_site(input_path: Path, output_dir: Path) -> None:
    rows = load_rows(input_path)
    assets_dir, charts_dir = ensure_dirs(output_dir)
    write_styles(assets_dir / "styles.css")

    overall = salary_stats(rows)
    monthly = numeric_values(rows, "monthly_wage")
    total = numeric_values(rows, "total")
    histogram(charts_dir / "monthly_distribution.svg", "月薪分布", monthly, "萬元")
    histogram(charts_dir / "total_distribution.svg", "年薪分布", total, "萬元")

    category_groups = group_rows(rows, "company_category")
    role_groups = group_rows(rows, "tittle")
    industry_rows = grouped_table(category_groups)
    industry_stable_rows, industry_small_rows = split_sample_rows(industry_rows)
    industry_stable_display_rows = relabel_first_column(industry_stable_rows, INDUSTRY_LABELS)
    industry_small_display_rows = relabel_first_column(industry_small_rows, INDUSTRY_LABELS)
    role_rows = grouped_table(role_groups)
    role_stable_rows, role_small_rows = split_sample_rows(role_rows)

    bar_chart(
        charts_dir / "industry_total_median.svg",
        f"產業年薪中位數排行（n >= {MAIN_CHART_MIN_SAMPLES}）",
        [(industry_label(row[0]), float(row[4])) for row in industry_stable_rows],
        "萬",
    )
    bar_chart(
        charts_dir / "role_total_median.svg",
        f"職能年薪中位數排行（n >= {MAIN_CHART_MIN_SAMPLES}）",
        [(row[0], float(row[4])) for row in role_stable_rows],
        "萬",
    )

    exp_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        exp_groups[bucket_experience(parse_number(row["year_of_experience"]))].append(row)
    exp_order = ["0-1 年", "1-3 年", "3-5 年", "5-8 年", "8+ 年", "未知"]
    exp_rows = order_rows(
        grouped_table({key: exp_groups[key] for key in exp_order if exp_groups.get(key)}),
        exp_order,
    )
    exp_line_items = []
    for key in exp_order:
        if key == "未知":
            continue
        if exp_groups.get(key):
            exp_line_items.append((key, salary_stats(exp_groups[key])["total_median"]))
    regression_points = []
    for row in rows:
        yoe = parse_number(row["year_of_experience"])
        total_salary = parse_number(row["total"])
        if yoe is not None and total_salary is not None and 0 <= yoe <= 8:
            regression_points.append((yoe, total_salary))
    early_career_regression = linear_regression(regression_points)
    regression_line_items = []
    bucket_midpoints = {"0-1 年": 0.5, "1-3 年": 2, "3-5 年": 4, "5-8 年": 6.5, "8+ 年": 8}
    for label, _ in exp_line_items:
        yoe = bucket_midpoints[label]
        predicted = early_career_regression["intercept"] + early_career_regression["slope"] * yoe
        regression_line_items.append((label, predicted))
    line_chart(
        charts_dir / "experience_total_median.svg",
        "年資與年薪中位數（排除未知年資）",
        exp_line_items,
        "萬元",
        comparison=regression_line_items,
        comparison_label="0-8 年回歸估算",
    )
    exp_stable_rows, exp_small_rows = split_sample_rows(exp_rows)

    bucket_order = experience_bucket_order()
    company_rows = [row for row in rows if row["company"] == COMPANY_SOURCE_NAME]
    company_category_rows = [row for row in rows if row["company_category"] == COMPANY_CATEGORY_NAME]
    company_summary = summarize_by_bucket(company_rows, bucket_order)
    industry_summary = summarize_by_bucket(company_category_rows, bucket_order)
    overall_summary = summarize_by_bucket(rows, bucket_order)
    monthly_series = [
        (COMPANY_DISPLAY_NAME, [company_summary[bucket]["monthly"] or None for bucket in bucket_order]),
        ("同產業", [industry_summary[bucket]["monthly"] or None for bucket in bucket_order]),
        ("全市場", [overall_summary[bucket]["monthly"] or None for bucket in bucket_order]),
    ]
    total_series = [
        (COMPANY_DISPLAY_NAME, [company_summary[bucket]["total"] or None for bucket in bucket_order]),
        ("同產業", [industry_summary[bucket]["total"] or None for bucket in bucket_order]),
        ("全市場", [overall_summary[bucket]["total"] or None for bucket in bucket_order]),
    ]
    multi_line_chart(charts_dir / "company_monthly_vs_market.svg", "年資月薪對照", bucket_order, monthly_series, "萬元")
    multi_line_chart(charts_dir / "company_total_vs_market.svg", "年資年薪對照", bucket_order, total_series, "萬元")

    industry_gap_rows = cohort_gap_table(rows, "company_category")
    industry_gap_display_rows = relabel_first_column(industry_gap_rows, INDUSTRY_LABELS)
    role_gap_rows = cohort_gap_table(rows, "tittle")
    bar_chart(
        charts_dir / "industry_experience_gap.svg",
        "產業 5+ 年相對 0-5 年年薪差距",
        [(industry_label(row[0]), float(row[5])) for row in industry_gap_rows],
        "萬",
    )
    bar_chart(
        charts_dir / "role_experience_gap.svg",
        "職能 5+ 年相對 0-5 年年薪差距",
        [(row[0], float(row[5])) for row in role_gap_rows],
        "萬",
    )

    high_cutoff = percentile(total, 0.9)
    high_rows = [row for row in rows if parse_number(row["total"]) is not None and parse_number(row["total"]) >= high_cutoff]
    high_detail_rows = [
        [
            row["company"],
            industry_label(row["company_category"]),
            row["tittle"],
            row["year_of_experience"],
            row["monthly_wage"],
            row["bonus"],
            row["total"],
        ]
        for row in sorted(high_rows, key=lambda item: parse_number(item["total"]) or 0, reverse=True)
    ]
    high_category = Counter(row["company_category"] for row in high_rows)
    high_role = Counter(row["tittle"] for row in high_rows)
    top_high_category, top_high_category_count = high_category.most_common(1)[0]
    top_high_role, top_high_role_count = high_role.most_common(1)[0]
    bar_chart(charts_dir / "high_salary_industry.svg", "高薪樣本產業分布", [(industry_label(k), v) for k, v in high_category.most_common()], "筆")
    bar_chart(charts_dir / "high_salary_role.svg", "高薪樣本職能分布", [(k, v) for k, v in high_role.most_common()], "筆")

    category_share = Counter(row["company_category"] for row in rows)
    role_share = Counter(row["tittle"] for row in rows)
    bar_chart(charts_dir / "category_sample_count.svg", "產業樣本數", [(industry_label(k), v) for k, v in category_share.most_common()], "筆")
    bar_chart(charts_dir / "role_sample_count.svg", "職能樣本數", [(k, v) for k, v in role_share.most_common(12)], "筆")

    output_dir.joinpath("index.html").write_text(page(
        SITE_TITLE,
        "index.html",
        f"""
<section><p class="lede">資料來源為 Dcard 上的匿名薪資樣本。本報告觀察台灣軟體工程市場在產業、職能與年資三個面向的薪資分布，協助判讀薪資帶、高薪樣本與成長節點。</p></section>
{insight_box("分析見解", [
    "514 筆樣本的月薪中位數為 6.5 萬、年薪中位數為 91 萬；讀者可先用這兩個數字定位自己的市場區間。",
    "職能樣本集中在 software engineer，共 297 筆；這個角色是本報告最主要的薪資基準。",
    "產業樣本以 IT 服務 131 筆、軟體 / 網路 107 筆、半導體 / 電子 72 筆為主；比較薪資時應先對齊產業，再比較職能與年資。",
])}
{stat_cards(overall)}
<section>
  <h2>怎麼讀這份報告</h2>
  <p class="lede">先用總覽的月薪與年薪中位數定位自己，再進入產業、職能與年資頁拆解差距；若目標是進入高薪區間，最後閱讀高薪樣本與行動建議，把下一步能力投資排進職涯計畫。</p>
</section>
<section class="chart-grid">
  <figure class="chart"><img src="assets/charts/monthly_distribution.svg" alt="月薪分布">{chart_note("單位為萬元；中位數比平均數更適合作為個人薪資定位基準。")}</figure>
  <figure class="chart"><img src="assets/charts/total_distribution.svg" alt="年薪分布">{chart_note("年薪以月薪乘上十二個月加 bonus 月數估算；右尾代表高薪樣本集中區。")}</figure>
</section>
<section class="chart-grid">
  <figure class="chart"><img src="assets/charts/category_sample_count.svg" alt="產業樣本數">{chart_note("產業比較先看樣本數；主結論以樣本數達門檻的分類為準。")}</figure>
  <figure class="chart"><img src="assets/charts/role_sample_count.svg" alt="職能樣本數">{chart_note("職能樣本集中在 software engineer；其他職能需搭配表格樣本數判讀。")}</figure>
</section>
""",
    ), encoding="utf-8")

    output_dir.joinpath("industry.html").write_text(page(
        "產業薪資分析",
        "industry.html",
        f"""
<section><p class="lede">依產業分類比較月薪與年薪中位數。主要排名圖納入樣本數至少 {MAIN_CHART_MIN_SAMPLES} 筆的產業；小樣本分類保留在補充表。</p></section>
{insight_box("分析見解", [
    "區塊鏈 / 加密貨幣以年薪中位數 159 萬排第一；高薪策略可鎖定高變現、高技術門檻的產品型產業。",
    "軟體 / 網路有 107 筆、年薪中位數 112 萬；半導體 / 電子有 72 筆、年薪中位數 104.3 萬，兩者是工程職涯的主戰場。",
    "IT 服務有 131 筆但年薪中位數為 68.9 萬；若讀者以薪資成長為優先，轉向產品型軟體、資安或半導體職缺會拉高上限。",
])}
<section><figure class="chart"><img src="assets/charts/industry_total_median.svg" alt="產業年薪中位數排行">{chart_note(f"圖中只呈現樣本數至少 {MAIN_CHART_MIN_SAMPLES} 筆的產業；小樣本分類列在補充表。")}</figure></section>
<section>
  <h2>主要產業樣本</h2>
  {table(["產業", "樣本數", "月薪中位數", "月薪 P25-P75", "年薪中位數", "年薪 P25-P75"], industry_stable_display_rows)}
</section>
<section>
  <h2>小樣本補充</h2>
  {table(["產業", "樣本數", "月薪中位數", "月薪 P25-P75", "年薪中位數", "年薪 P25-P75"], industry_small_display_rows)}
</section>
""",
    ), encoding="utf-8")

    output_dir.joinpath("role.html").write_text(page(
        "職能薪資分析",
        "role.html",
        f"""
<section><p class="lede">依標準化職稱比較薪資。主要排名圖只納入樣本數至少 {MAIN_CHART_MIN_SAMPLES} 筆的職能；所有職能仍保留在表格中。</p></section>
{insight_box("分析見解", [
    "software engineer 有 297 筆，是最大宗職能；年薪中位數 98 萬，高於 backend、frontend、mobile 等主要工程職能。",
    "主要職能中，backend engineer 有 50 筆、frontend engineer 有 45 筆，但年薪中位數分別為 84 萬與 72.7 萬，低於 software engineer。",
    "5 年前後差距以 product manager 最明顯：0-5 年中位數 70 萬、5+ 年 139.2 萬；software engineer 也從 78.2 萬拉到 128 萬。",
])}
<section><figure class="chart"><img src="assets/charts/role_total_median.svg" alt="職能年薪中位數排行">{chart_note(f"圖中只呈現樣本數至少 {MAIN_CHART_MIN_SAMPLES} 筆的職能；排序以年薪中位數為主。")}</figure></section>
<section>
  <h2>主要職能樣本</h2>
  {table(["職能", "樣本數", "月薪中位數", "月薪 P25-P75", "年薪中位數", "年薪 P25-P75"], role_stable_rows)}
</section>
<section>
  <h2>小樣本補充</h2>
  {table(["職能", "樣本數", "月薪中位數", "月薪 P25-P75", "年薪中位數", "年薪 P25-P75"], role_small_rows)}
</section>
""",
    ), encoding="utf-8")

    output_dir.joinpath("experience.html").write_text(page(
        "年資薪資分析",
        "experience.html",
        f"""
<section><p class="lede">以總年資分箱觀察薪資變化。年薪中位數從 1-3 年的 71.5 萬，提升到 5-8 年的 112 萬與 8+ 年的 137.1 萬。</p></section>
{insight_box("分析見解", [
    "1-3 年年薪中位數為 71.5 萬，3-5 年為 84 萬；前三到五年應優先累積可展示的技術深度與完整交付經驗。",
    "5-8 年年薪中位數達 112 萬，比 3-5 年增加 28 萬；這個區間是從執行者轉向獨立負責模組與系統設計的薪資分水嶺。",
    "8+ 年年薪中位數達 137.1 萬，P75 達 185.2 萬；資深工程師要把影響力延伸到架構決策、跨團隊協作與人才培養。",
])}
<section>
  <h2>主要觀察</h2>
  <p class="lede">年資提升帶來的薪資差距集中在責任範圍升級。讀者在 3-5 年前要完成技術基礎與專案交付紀錄；進入 5-8 年後，薪資競爭力來自系統設計、故障排除、跨團隊推進與技術判斷。</p>
</section>
<section class="insight">
  <h2>1-3 年低於 0-1 年的解讀</h2>
  <ul><li>來源：Gemini。0-1 年樣本容易集中在高起薪族群，例如半導體、外商與頂尖軟體工程職缺；這會拉高新鮮人區間的中位數。</li><li>1-3 年樣本涵蓋更多產業與職能，包含中小型企業、傳統產業與轉職初期工作者；樣本組成變廣後，中位數會往市場基準收斂。</li><li>這不代表工作第二年薪水會倒退。更實用的解讀是：1-5 年是累積與換位期，5 年後能主導系統、跨團隊交付或轉向高薪產業的人，薪資級距開始拉開。</li></ul>
</section>
<section class="insight">
  <h2>0-8 年回歸估算</h2>
  <ul><li>以 0-8 年共 {int(early_career_regression['count'])} 筆樣本做簡單線性迴歸，估算公式為：年薪 = {fmt(early_career_regression['intercept'])} + {fmt(early_career_regression['slope'])} × 年資（萬元）。</li><li>係數解讀：0-8 年區間內，年資每增加 1 年，年薪估算值增加 {fmt(early_career_regression['slope'])} 萬。</li><li>模型 R² 為 {fmt(early_career_regression['r2'], 2)}；年資提供基準線，產業、職能、公司層級與跳槽時點決定實際落點。</li></ul>
</section>
<section><figure class="chart"><img src="assets/charts/experience_total_median.svg" alt="年資與年薪中位數">{chart_note("圖表排除未知年資；年資區間的核心解讀是責任範圍升級帶來的薪資差距。")}</figure></section>
<section>
  <h2>年資區間統計</h2>
  {table(["年資區間", "樣本數", "月薪中位數", "月薪 P25-P75", "年薪中位數", "年薪 P25-P75"], exp_stable_rows)}
</section>
<section>
  <h2>小樣本補充</h2>
  {table(["年資區間", "樣本數", "月薪中位數", "月薪 P25-P75", "年薪中位數", "年薪 P25-P75"], exp_small_rows)}
</section>
""",
    ), encoding="utf-8")

    company_stats = salary_stats(company_rows)
    industry_stats = salary_stats(company_category_rows)
    overall_stats = salary_stats(rows)
    company_comparison_rows = [
        ["樣本數", str(int(company_stats["count"])), str(int(industry_stats["count"])), str(int(overall_stats["count"]))],
        ["月薪中位數", f"{fmt(company_stats['monthly_median'])} 萬", f"{fmt(industry_stats['monthly_median'])} 萬", f"{fmt(overall_stats['monthly_median'])} 萬"],
        ["年薪中位數", f"{fmt(company_stats['total_median'])} 萬", f"{fmt(industry_stats['total_median'])} 萬", f"{fmt(overall_stats['total_median'])} 萬"],
        ["月薪差距（相對同產業）", f"{fmt(company_stats['monthly_median'] - industry_stats['monthly_median'])} 萬", "-", "-"],
        ["年薪差距（相對同產業）", f"{fmt(company_stats['total_median'] - industry_stats['total_median'])} 萬", "-", "-"],
    ]
    company_vs_industry_rows = []
    company_vs_market_rows = []
    for bucket in bucket_order:
        c = company_summary[bucket]
        i = industry_summary[bucket]
        o = overall_summary[bucket]
        if c["count"] or i["count"]:
            company_vs_industry_rows.append([
                bucket,
                str(int(c["count"])),
                f"{fmt(c['monthly'])} 萬" if c["count"] else "-",
                f"{fmt(c['total'])} 萬" if c["count"] else "-",
                str(int(i["count"])),
                f"{fmt(i['monthly'])} 萬" if i["count"] else "-",
                f"{fmt(i['total'])} 萬" if i["count"] else "-",
            ])
        if c["count"] or o["count"]:
            company_vs_market_rows.append([
                bucket,
                str(int(c["count"])),
                f"{fmt(c['monthly'])} 萬" if c["count"] else "-",
                f"{fmt(c['total'])} 萬" if c["count"] else "-",
                str(int(o["count"])),
                f"{fmt(o['monthly'])} 萬" if o["count"] else "-",
                f"{fmt(o['total'])} 萬" if o["count"] else "-",
            ])

    output_dir.joinpath("company.html").write_text(page(
        COMPANY_DISPLAY_NAME,
        "company.html",
        f"""
<section><p class="lede">這頁把一間 SaaS 公司的薪資樣本當作案例，示範如何用同產業與全市場基準判讀公司薪資位置。公司樣本數為 {int(company_stats['count'])} 筆。</p></section>
{insight_box("分析見解", [
    f"案例公司月薪中位數為 {fmt(company_stats['monthly_median'])} 萬、年薪中位數為 {fmt(company_stats['total_median'])} 萬；年薪低於同產業中位數 {fmt(industry_stats['total_median'])} 萬 21.7 萬。",
    "1-3 年與 3-5 年區間的公司年薪中位數分別為 78 萬與 91 萬，與同產業相同；早中期薪資位置貼近同產業基準。",
    "5-8 年公司年薪中位數為 93.6 萬，低於同產業 126 萬；8+ 年為 114.4 萬，低於同產業 175 萬。資深階段的薪資上限是主要差距。",
])}
<section class="chart-grid">
  <figure class="chart"><img src="assets/charts/company_monthly_vs_market.svg" alt="公司月薪與市場對照">{chart_note("月薪折線用來看各年資區間是否貼近同產業基準。")}</figure>
  <figure class="chart"><img src="assets/charts/company_total_vs_market.svg" alt="公司年薪與市場對照">{chart_note("年薪折線納入 bonus 影響；資深區間差距會比月薪更明顯。")}</figure>
</section>
<section>
  <h2>整體對照</h2>
  {table(["指標", f"{COMPANY_DISPLAY_NAME}", "同產業", "全市場"], company_comparison_rows)}
</section>
<section>
  <h2>案例對同產業</h2>
  <div class="table-scroll">{table(["年資", "案例樣本", "案例月薪", "案例年薪", "同產業樣本", "同產業月薪", "同產業年薪"], company_vs_industry_rows)}</div>
</section>
<section>
  <h2>案例對全市場</h2>
  <div class="table-scroll">{table(["年資", "案例樣本", "案例月薪", "案例年薪", "全市場樣本", "全市場月薪", "全市場年薪"], company_vs_market_rows)}</div>
</section>
""",
    ), encoding="utf-8")

    output_dir.joinpath("cross_analysis.html").write_text(page(
        "年資 × 產業 × 職能",
        "cross_analysis.html",
        f"""
<section><p class="lede">這頁把年資拆進產業與職能，比較 0-5 年與 5+ 年的年薪中位數差距。差距排行納入兩邊各至少 {CROSS_ANALYSIS_MIN_SAMPLES} 筆的群組。</p></section>
{insight_box("分析見解", [
    "產業差距最大的是半導體 / 電子：0-5 年年薪中位數 91 萬、5+ 年 144 萬，差距 53 萬。",
    "軟體 / 網路從 91 萬提升到 136.5 萬，差距 45.5 萬；資深階段的議價能力集中在產品型軟體與平台型公司。",
    "職能差距最大的是 product manager，從 70 萬提升到 139.2 萬；software engineer 從 78.2 萬提升到 128 萬，是工程職涯最穩定的成長主軸。",
])}
<section class="chart-grid">
  <figure class="chart"><img src="assets/charts/industry_experience_gap.svg" alt="產業年資薪資差距">{chart_note(f"圖表納入 0-5 年與 5+ 年兩側各至少 {CROSS_ANALYSIS_MIN_SAMPLES} 筆的產業。")}</figure>
  <figure class="chart"><img src="assets/charts/role_experience_gap.svg" alt="職能年資薪資差距">{chart_note(f"圖表納入 0-5 年與 5+ 年兩側各至少 {CROSS_ANALYSIS_MIN_SAMPLES} 筆的職能。")}</figure>
</section>
<section>
  <h2>產業：0-5 年 vs 5+ 年</h2>
  <div class="table-scroll">{table(["產業", "0-5 年樣本", "0-5 年中位數", "5+ 年樣本", "5+ 年中位數", "差距", "倍數"], industry_gap_display_rows)}</div>
</section>
<section>
  <h2>職能：0-5 年 vs 5+ 年</h2>
  <div class="table-scroll">{table(["職能", "0-5 年樣本", "0-5 年中位數", "5+ 年樣本", "5+ 年中位數", "差距", "倍數"], role_gap_rows)}</div>
</section>
""",
    ), encoding="utf-8")

    high_stats = salary_stats(high_rows)
    output_dir.joinpath("high_salary.html").write_text(page(
        "高薪樣本分析",
        "high_salary.html",
        f"""
<section><p class="lede">高薪樣本定義為年薪前 10%，門檻為 {fmt(high_cutoff)} 萬。此頁呈現高薪樣本的產業與職能分布。</p></section>
{stat_cards(high_stats)}
{insight_box("分析見解", [
    f"高薪樣本共有 {int(high_stats['count'])} 筆，年薪中位數為 {fmt(high_stats['total_median'])} 萬；這是讀者評估高薪門檻的主要參考線。",
    f"產業分布以 {industry_label(top_high_category)} 最多，共 {top_high_category_count} 筆；高薪職涯集中在產品型軟體、平台與高技術密度產業。",
    f"職能分布以 {top_high_role} 最多，共 {top_high_role_count} 筆；工程師要進入高薪區間，核心能力是系統設計、商業影響力與跨團隊交付。",
])}
<section class="chart-grid">
  <figure class="chart"><img src="assets/charts/high_salary_industry.svg" alt="高薪樣本產業分布">{chart_note("高薪樣本為年薪前 10%；產業分布用來定位高薪機會集中處。")}</figure>
  <figure class="chart"><img src="assets/charts/high_salary_role.svg" alt="高薪樣本職能分布">{chart_note("職能分布顯示高薪樣本以 software engineer 為主，能力投資仍回到工程深度與交付影響力。")}</figure>
</section>
<section>
  <h2>高薪樣本明細</h2>
  {table(["公司", "產業", "職能", "年資", "月薪", "Bonus", "年薪"], high_detail_rows)}
</section>
""",
    ), encoding="utf-8")

    output_dir.joinpath("actions.html").write_text(page(
        "年資行動建議",
        "actions.html",
        """
<section><p class="lede">這頁把薪資數據轉成職涯行動。讀者可依目前年資區間，選擇下一階段最該投入的能力。</p></section>
<section class="insight">
  <h2>行動主軸</h2>
  <ul><li>0-3 年：建立穩定交付能力，讓履歷能說清楚自己負責的功能、技術選型與上線結果。</li><li>3-5 年：主導模組與跨服務問題，開始累積系統設計、效能優化、測試與維運經驗。</li><li>5 年後：把影響力從個人產出擴大到架構決策、跨團隊協作、技術 mentoring 與商業指標。</li></ul>
</section>
<section>
  <h2>分階段建議</h2>
  <table>
    <thead><tr><th>年資</th><th>職涯定位</th><th>能力重點</th><th>下一步行動</th></tr></thead>
    <tbody>
      <tr><td>0-1 年</td><td>入門期</td><td>基礎工程能力、debug、測試、版本控制</td><td>建立 2-3 個可展示的完整交付案例，明確寫出影響範圍。</td></tr>
      <tr><td>1-3 年</td><td>成長期</td><td>穩定交付、需求拆解、API 與資料模型設計</td><td>爭取獨立負責功能模組，補齊後端、前端、雲端部署或資料庫能力。</td></tr>
      <tr><td>3-5 年</td><td>進階期</td><td>系統設計、效能、可靠性、跨團隊溝通</td><td>主動承接跨服務議題，讓履歷從「寫功能」升級成「解決系統問題」。</td></tr>
      <tr><td>5-8 年</td><td>資深期</td><td>架構判斷、技術取捨、事件處理、帶人</td><td>建立技術決策紀錄，累積設計審查、incident review、mentoring 經驗。</td></tr>
      <tr><td>8+ 年</td><td>領導期</td><td>技術策略、組織影響力、人才培養、商業指標</td><td>把成果連到營收、成本、穩定性或開發效率，建立資深職涯的議價籌碼。</td></tr>
    </tbody>
  </table>
</section>
<section>
  <h2>轉職檢核</h2>
  <table>
    <thead><tr><th>目標</th><th>檢核問題</th></tr></thead>
    <tbody>
      <tr><td>拉高薪資上限</td><td>目標職缺是否位在產品型軟體、半導體 / 電子、資安或高技術密度產業。</td></tr>
      <tr><td>轉向高薪職能</td><td>履歷是否能證明系統設計、跨團隊交付與 production ownership。</td></tr>
      <tr><td>資深職涯升級</td><td>面試故事是否從個人貢獻升級到技術決策、團隊槓桿與商業影響。</td></tr>
    </tbody>
  </table>
</section>
""",
    ), encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    build_site(args.input, args.output)
    print(f"Wrote static report to {args.output}")


if __name__ == "__main__":
    main()
