# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=2,<3",
#   "pandera[pandas]>=0.21,<0.27",
#   "pdfplumber>=0.11,<0.12",
#   "pydantic>=2,<3",
#   "requests>=2,<3",
# ]
# ///

import argparse
import io
import os
import re
from typing import Any, Dict, List, Optional

import pandas as pd
import pandera.pandas as pa
import pdfplumber
import requests
from pydantic import BaseModel

URL = "https://www.e-stat.go.jp/estat/html/tokei_itiran.pdf"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gov_stats_codes.csv")


class GovStatsCodes(pa.DataFrameModel):
    """政府統計コード一覧のスキーマ定義"""

    gov_stats_code: str = pa.Field(str_matches=r"^\d{8}$", description="政府統計コード")
    gov_stats_name: str = pa.Field(description="政府統計名")
    organization: str = pa.Field(description="作成機関")
    department: str = pa.Field(description="担当部局課室名")
    stats_type: str = pa.Field(description="統計の種類")
    cycle: str = pa.Field(description="提供周期")
    data_list_status: str = pa.Field(description="データ一覧登録状況")
    has_file: str = pa.Field(description="統計表ファイルの有無")
    has_db: str = pa.Field(description="データベースの有無")
    org_info: str = pa.Field(description="作成機関情報")
    org_info_link: Optional[str] = pa.Field(
        nullable=True, description="作成機関情報のリンク"
    )

    class Config:
        strict = True
        coerce = True


class GovStatsRecord(BaseModel):
    gov_stats_code: str
    gov_stats_name: str
    organization: str
    department: str
    stats_type: str
    cycle: str
    data_list_status: str
    has_file: str
    has_db: str
    org_info: str
    org_info_link: Optional[str] = None


def download_pdf(url: str) -> bytes:
    print(f"Downloading {url}...")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def extract_records_from_pdf(pdf_content: bytes) -> List[GovStatsRecord]:
    records = []

    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        print(f"Total pages: {len(pdf.pages)}")

        current_record: Dict[str, Any] = {}
        name_parts: List[str] = []

        for i, page in enumerate(pdf.pages):
            print(f"Processing page {i + 1}...")
            # Use find_tables to get Table objects which contain coordinates
            tables = page.find_tables(
                table_settings={
                    "vertical_strategy": "text",
                    "horizontal_strategy": "text",
                }
            )

            if not tables:
                print(f"No tables found on page {i + 1}")
                continue

            page_links = page.hyperlinks

            # Flatten all tables on the page (usually just one)
            for table in tables:
                # Extract text and get rows (with cells coordinates)
                text_rows = table.extract()
                cell_rows = table.rows

                # Ensure they have same length
                if len(text_rows) != len(cell_rows):
                    print(
                        f"Warning: Text rows ({len(text_rows)}) and cell rows "
                        f"({len(cell_rows)}) mismatch on page {i + 1}"
                    )
                    continue

                for text_row, cell_row in zip(text_rows, cell_rows):
                    # Get cells from Row object
                    cell_row_list = cell_row.cells

                    # Clean row data
                    clean_row = [str(cell).strip() if cell else "" for cell in text_row]

                    # Check if row is empty (separator)
                    is_empty = all(not cell for cell in clean_row)

                    # Logic to flush record
                    # 1. Empty line encountered
                    if is_empty:
                        if current_record:
                            current_record["gov_stats_name"] = "".join(name_parts)
                            records.append(GovStatsRecord(**current_record))
                            current_record = {}
                            name_parts = []
                        continue

                    first_col = clean_row[0]

                    # Check if it's a header row
                    if "政府統計" in first_col or "コード" in first_col:
                        continue

                    # Check if it's a Main Row (starts with 8-digit code)
                    if re.match(r"^\d{8}$", first_col):
                        # 2. New Code encountered AND current_record already has a Code -> flush previous
                        if current_record and "gov_stats_code" in current_record:
                            current_record["gov_stats_name"] = "".join(name_parts)
                            records.append(GovStatsRecord(**current_record))
                            current_record = {}
                            name_parts = []

                        # Handle merged columns (Department and Type)
                        # Case: ['00500000', 'Name', 'Org', 'Dept Type', 'Cycle', ...] (Len 9)
                        org_info_cell_index = 9  # Default

                        if len(clean_row) == 9:
                            # Check 4th column (index 3) for merger
                            possible_merged = clean_row[3]
                            known_types = [
                                "一般統計",
                                "業務統計",
                                "加工統計",
                                "基幹統計",
                                "その他",
                            ]
                            for kt in known_types:
                                if possible_merged.endswith(kt):
                                    # Split found
                                    dept = possible_merged[: -len(kt)].strip()
                                    stat_type = kt
                                    # Reconstruct row
                                    clean_row = (
                                        clean_row[:3]
                                        + [dept, stat_type]
                                        + clean_row[4:]
                                    )
                                    org_info_cell_index = 8  # Shifted
                                    break

                        # Populate main fields
                        # Ensure row has enough columns (pad if necessary)
                        if len(clean_row) < 10:
                            clean_row += [""] * (10 - len(clean_row))

                        current_record["gov_stats_code"] = clean_row[0]
                        current_record["organization"] = clean_row[2]
                        current_record["department"] = clean_row[3]
                        current_record["stats_type"] = clean_row[4]
                        current_record["cycle"] = clean_row[5]
                        current_record["data_list_status"] = clean_row[6]
                        current_record["has_file"] = clean_row[7]
                        current_record["has_db"] = clean_row[8]
                        current_record["org_info"] = clean_row[9]
                        current_record["org_info_link"] = None

                        # Extract Link for 'org_info'
                        # cell_row_list[org_info_cell_index] is the rect (x0, top, x1, bottom)
                        if len(cell_row_list) > org_info_cell_index:
                            target_cell = cell_row_list[org_info_cell_index]
                            if target_cell:  # target_cell might be None if merged or empty?
                                # Find matching link
                                for link in page_links:
                                    # Check if link center is within cell
                                    l_x = (link["x0"] + link["x1"]) / 2
                                    l_y = (link["top"] + link["bottom"]) / 2

                                    # target_cell is (x0, top, x1, bottom)
                                    if (
                                        target_cell[0] <= l_x <= target_cell[2]
                                        and target_cell[1] <= l_y <= target_cell[3]
                                    ):
                                        current_record["org_info_link"] = link["uri"]
                                        break

                        # Add name part if exists on this row
                        if clean_row[1]:
                            name_parts.append(clean_row[1])

                    else:
                        # Continuation row or Pre-code name row
                        if len(clean_row) > 1 and clean_row[1]:
                            name_parts.append(clean_row[1])
                        elif len(clean_row) > 0 and clean_row[0]:
                            name_parts.append(clean_row[0])

        # Flush last record
        if current_record:
            current_record["gov_stats_name"] = "".join(name_parts)
            records.append(GovStatsRecord(**current_record))

    return records


def records_to_dataframe(records: List[GovStatsRecord]) -> pd.DataFrame:
    df = pd.DataFrame([r.model_dump() for r in records])

    # Reorder columns based on schema definition.
    schema_columns = list(GovStatsCodes.to_schema().columns.keys())
    for col in schema_columns:
        if col not in df.columns:
            df[col] = None
    return df[schema_columns]


def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    print("Validating with Pandera...")
    try:
        validated_df = GovStatsCodes.validate(df, lazy=True)
    except pa.errors.SchemaErrors as err:
        print("Schema errors:", err.failure_cases, file=sys.stderr)
        raise
    print("Validation successful!")
    return validated_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download e-Stat government statistics code PDF and export it as CSV."
    )
    parser.add_argument(
        "--url",
        default=URL,
        help=f"PDF URL to download. Default: {URL}",
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_FILE,
        help=f"CSV output path. Default: {OUTPUT_FILE}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_content = download_pdf(args.url)
    records = extract_records_from_pdf(pdf_content)

    print(f"Extracted {len(records)} records.")

    df = records_to_dataframe(records)
    validated_df = validate_dataframe(df)

    print(f"Saving to {args.output}...")
    validated_df.to_csv(args.output, index=False)
    print("Done.")


if __name__ == "__main__":
    main()
