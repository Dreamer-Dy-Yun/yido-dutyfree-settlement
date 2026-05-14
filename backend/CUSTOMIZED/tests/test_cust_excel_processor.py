import pandas as pd

from CUSTOMIZED.cust_excel_processor import ExcelProcessor


def test_flatten_columns_handles_non_string_header_levels():
    processor = ExcelProcessor.__new__(ExcelProcessor)
    columns = pd.MultiIndex.from_tuples(
        [
            ("No", 1),
            ("Amount", "USD"),
            ("Unnamed: 2_level_0", "memo"),
        ]
    )

    flattened = processor._flatten_columns(columns)

    assert flattened == ["No[>]1", "Amount[>]USD", "memo"]
