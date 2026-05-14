import pandas as pd

from PROCESSOR_DATA.parsers.edi_lotte import EdiLotte
from PROCESSOR_DATA.parsers.edi_silla import EdiSilla


def _source_row(processor, overrides_by_target):
    row = {}
    for source_col, (target_col, dtype) in processor.column_spec().items():
        if target_col in overrides_by_target:
            row[source_col] = overrides_by_target[target_col]
        elif dtype == "Int64":
            row[source_col] = 1
        elif dtype == "float64":
            row[source_col] = 10.5
        elif dtype.startswith("datetime64"):
            row[source_col] = "2025-01-02"
        else:
            row[source_col] = f"{target_col}-value"
    return row


def test_edi_lotte_parse_and_unified_contract():
    processor = EdiLotte()
    row = _source_row(
        processor,
        {
            "branch": "Myeongdong",
            "original_sales_date": "2025-01-01",
            "sales_date": "2025-01-02",
            "customer_name": "Customer A",
            "group_no": "G-1",
            "voucher_no": "V-001",
            "product_code": "SKU-001",
            "sales_quantity": 2.0,
        },
    )

    parsed = processor.set_data(pd.DataFrame([row])).parse()
    unified = processor.to_unified(parsed)

    assert parsed.loc[0, "voucher_no"] == "V-001"
    assert parsed.loc[0, "product_code"] == "SKU-001"
    assert unified.loc[0, "dutyfree_operator"] == "LOTTE"
    assert unified.loc[0, "receipt_no"] == "V-001"
    assert unified.loc[0, "product_code"] == "SKU-001"
    assert unified.loc[0, "manufactured_at"] is None


def test_edi_silla_parse_and_unified_contract_with_dd00_aging():
    processor = EdiSilla()
    row = _source_row(
        processor,
        {
            "branch": "Seoul",
            "original_sales_date": "2025-01-01",
            "sales_date": "2025-01-02",
            "customer_name": "Customer B",
            "group_no": "G-2",
            "bill_no": "B-001",
            "product_code": "SKU-002",
            "aging": "250100",
            "sales_quantity": 3.0,
        },
    )

    parsed = processor.set_data(pd.DataFrame([row])).parse()
    unified = processor.to_unified(parsed)

    assert parsed.loc[0, "bill_no"] == "B-001"
    assert parsed.loc[0, "aging"] == "250100"
    assert unified.loc[0, "dutyfree_operator"] == "SILLA"
    assert unified.loc[0, "receipt_no"] == "B-001"
    assert unified.loc[0, "product_code"] == "SKU-002"
    assert unified.loc[0, "manufactured_at"] == pd.Timestamp("2025-01-01")
    assert unified.loc[0, "system_note"] is None
