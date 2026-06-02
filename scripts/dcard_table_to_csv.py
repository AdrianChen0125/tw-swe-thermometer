#!/usr/bin/env python3
from __future__ import annotations

import argparse
from io import StringIO
from pathlib import Path

import pandas as pd
from paddleocr import PPStructureV3


TARGET_COLUMNS = [
    "Created_date",
    "company",
    "tittle",
    "year_of_experience",
    "Seniority",
    "monthly_wage",
    "bonus",
    "total",
]


def pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    normalized = {str(c).strip(): c for c in df.columns}
    for key, original in normalized.items():
        for c in candidates:
            if c in key:
                return original
    return None


def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping_rules = {
        "Created_date": ["時間戳記", "建立時間", "created", "date"],
        "company": ["公司名稱", "公司"],
        "tittle": ["職務", "職稱", "title"],
        "year_of_experience": ["相關年資", "總年資", "年資"],
        "Seniority": ["現職年資", "seniority"],
        "monthly_wage": ["月底薪", "月薪", "monthly"],
        "bonus": ["bonus", "獎金", "幾個月"],
        "total": ["總年薪", "年薪", "total"],
    }

    output = pd.DataFrame()
    for target, keys in mapping_rules.items():
        col = pick_column(df, keys)
        if col is None:
            output[target] = ""
        else:
            output[target] = df[col].astype(str).str.strip()

    return output[TARGET_COLUMNS]


def extract_tables_from_image(engine: PPStructureV3, image_path: Path) -> list[pd.DataFrame]:
    result = engine.predict(str(image_path))
    tables: list[pd.DataFrame] = []
    for page in result:
        for table in page.get("table_res_list", []):
            html = table.get("pred_html")
            if not html:
                continue
            parsed = pd.read_html(StringIO(html))
            tables.extend(parsed)
    return tables


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    image_paths = sorted(args.input_dir.glob("*.png"))
    engine = PPStructureV3(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
    )

    all_rows: list[pd.DataFrame] = []
    for image_path in image_paths:
        tables = extract_tables_from_image(engine, image_path)
        for t in tables:
            out = map_columns(t)
            out["__source_file"] = image_path.name
            all_rows.append(out)

    if not all_rows:
        raise RuntimeError("No table detected. Check image quality or input path.")

    merged = pd.concat(all_rows, ignore_index=True)
    merged = merged.replace({"nan": "", "None": ""})
    merged = merged[merged["company"].astype(str).str.strip() != ""]
    merged = merged[TARGET_COLUMNS]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"Wrote {len(merged)} rows to {args.output}")


if __name__ == "__main__":
    main()
