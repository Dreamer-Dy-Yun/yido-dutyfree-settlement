# compare_parquet_to_excel.py
from __future__ import annotations
import pandas as pd
import numpy as np

def _is_float_dtype(s: pd.Series) -> bool:
    return pd.api.types.is_float_dtype(s)

def _compare_series(s1: pd.Series, s2: pd.Series, *, rtol: float, atol: float) -> pd.Series:
    """두 시리즈 비교 -> 다르면 True"""
    if _is_float_dtype(s1) or _is_float_dtype(s2):
        a = pd.to_numeric(s1, errors="coerce").astype("float64")
        b = pd.to_numeric(s2, errors="coerce").astype("float64")
        eq = np.isclose(a.values, b.values, rtol=rtol, atol=atol, equal_nan=True)
        return ~pd.Series(eq, index=s1.index)

    s1_na = s1.isna()
    s2_na = s2.isna()
    diff = s1_na ^ s2_na
    both_val = ~s1_na & ~s2_na
    comp = s1[both_val].values != s2[both_val].values
    diff.loc[both_val] = comp
    return diff

def compare_parquet_to_excel(
    left_path: str,
    right_path: str,
    *,
    engine: str = "pyarrow",
    rtol: float = 1e-7,
    atol: float = 0.0,
    out_csv: str | None = None,           # 선택: CSV도 함께 저장
    out_xlsx: str = "parquet_diff_report.xlsx",   # 엑셀 파일 경로
    excel_engine: str = "openpyxl",       # 또는 "xlsxwriter"
) -> dict:
    """
    두 Parquet 파일을 1:1 비교하고, 결과를 Excel로 저장한다.
    시트: diff_report / left_data / right_data
    반환: {'diff_mask': DataFrame, 'summary': DataFrame, 'report_df': DataFrame}
    """
    # 1) 로드
    df1 = pd.read_parquet(left_path, engine=engine)
    df2 = pd.read_parquet(right_path, engine=engine)

    # 2) 전제 검증
    if list(df1.columns) != list(df2.columns):
        raise ValueError(
            "Column mismatch.\n"
            f"left columns : {list(df1.columns)}\n"
            f"right columns: {list(df2.columns)}"
        )
    if len(df1) != len(df2):
        raise ValueError(f"Row count mismatch: left={len(df1)}, right={len(df2)}")

    # 3) 인덱스 동기화
    df1 = df1.reset_index(drop=True)
    df2 = df2.reset_index(drop=True)

    # 4) 차이 마스크
    diff_cols = {col: _compare_series(df1[col], df2[col], rtol=rtol, atol=atol) for col in df1.columns}
    diff_mask = pd.DataFrame(diff_cols)

    # 5) 상세 리포트(서로 다른 셀만)
    rows, cols = np.where(diff_mask.values)
    if rows.size > 0:
        records = []
        for r, c in zip(rows, cols):
            col = diff_mask.columns[c]
            v1 = df1.iloc[r, c]
            v2 = df2.iloc[r, c]
            records.append({"row_index": r, "column": col, "left_value": v1, "right_value": v2})
        report_df = pd.DataFrame(records).sort_values(["row_index", "column"], ignore_index=True)
    else:
        report_df = pd.DataFrame(columns=["row_index", "column", "left_value", "right_value"])

    # (선택) CSV도 저장
    if out_csv:
        report_df.to_csv(out_csv, index=False, encoding="utf-8")

    # 6) 요약
    per_col_counts = diff_mask.sum(axis=0).rename("diff_cells")
    per_col_rows = diff_mask.any(axis=0).rename("has_any_diff").astype(bool)
    summary = pd.concat([per_col_counts, per_col_rows], axis=1)
    total_cells = diff_mask.size
    total_diff = int(diff_mask.values.sum())
    diff_rows = int(diff_mask.any(axis=1).sum())

    # 7) 엑셀 저장
    with pd.ExcelWriter(out_xlsx, engine=excel_engine) as writer:
        report_df.to_excel(writer, sheet_name="diff_report", index=False)
        df1.to_excel(writer, sheet_name="left_data", index=False)
        df2.to_excel(writer, sheet_name="right_data", index=False)

        # 보조 요약 시트(원하시면 제거 가능)
        meta = pd.DataFrame(
            {
                "metric": [
                    "left_path", "right_path",
                    "rows", "cols", "total_cells", "diff_cells", "rows_with_any_diff",
                    "rtol", "atol"
                ],
                "value": [
                    left_path, right_path,
                    len(df1), df1.shape[1], total_cells, total_diff, diff_rows,
                    rtol, atol
                ],
            }
        )
        meta.to_excel(writer, sheet_name="summary", index=False)
        summary.reset_index(names="column").to_excel(writer, sheet_name="summary", index=False, startrow=len(meta) + 2)

    print("=== Parquet 1:1 Diff Summary ===")
    print(f"- Files: '{left_path}' vs '{right_path}'")
    print(f"- Shape: rows={len(df1)}, cols={df1.shape[1]}")
    print(f"- Total cells: {total_cells:,}, Diff cells: {total_diff:,}, Rows with any diff: {diff_rows:,}")
    if total_diff > 0:
        print(f"- Detailed differences: {len(report_df):,} cells")
    print(f"- Excel saved to: {out_xlsx}")
    if out_csv:
        print(f"- CSV saved to: {out_csv}")

    return {"diff_mask": diff_mask, "summary": summary, "report_df": report_df}



if __name__ == "__main__":
    compare_parquet_to_excel(
        r"C:\Users\user\Novas_Ez\TEST\SPEC\test_name_DB92-05606A(20250901 170007).parquet",
        r"C:\Users\user\Novas_Ez\TEST\SPEC\test_name_DB92-05606A(20250910 144931).parquet",
        rtol=1e-7,
        atol=0.0,
        out_csv=r"C:\Users\user\OneDrive\Desktop\diff_report.csv",
        out_xlsx=r"C:\Users\user\OneDrive\Desktop\parquet_diff_report.xlsx",
        excel_engine="openpyxl",  # 또는 "xlsxwriter"
    )
    pass
