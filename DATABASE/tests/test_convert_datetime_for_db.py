import pandas as pd
from datetime import datetime

from DATABASE.dbms.postgre.pg_manager import PGDBManager


def main() -> None:
    # 원본 DataFrame: datetime64 컬럼 + 일반 컬럼 섞어서 생성
    df = pd.DataFrame(
        {
            "dt_col": [
                pd.Timestamp("2024-09-21 00:00:00"),
                pd.NaT,
                pd.Timestamp("2024-09-23 12:34:56"),
            ],
            "str_col": ["a", "b", None],
            "int_col": [1, 2, None],
        }
    )

    print("=== original df ===")
    print(df)
    print("\n=== original dtypes ===")
    print(df.dtypes)

    # deep_copy=True
    df_converted_deep = PGDBManager.convert_datetime_for_db(df, deep_copy=True)
    print("\n=== converted (deep_copy=True) df ===")
    print(df_converted_deep)
    print("\n=== converted (deep_copy=True) dtypes ===")
    print(df_converted_deep.dtypes)
    print("\n=== sample types (deep_copy=True) ===")
    for i, v in enumerate(df_converted_deep["dt_col"]):
        print(f"row {i}: value={v!r}, type={type(v)}")

    # deep_copy=False
    df_shallow = df.copy()
    df_converted_shallow = PGDBManager.convert_datetime_for_db(df_shallow, deep_copy=False)
    print("\n=== converted (deep_copy=False) df ===")
    print(df_converted_shallow)
    print("\n=== converted (deep_copy=False) dtypes ===")
    print(df_converted_shallow.dtypes)
    print("\n=== sample types (deep_copy=False) ===")
    for i, v in enumerate(df_converted_shallow["dt_col"]):
        print(f"row {i}: value={v!r}, type={type(v)}")

    # 원본 df 가 변했는지도 확인
    print("\n=== original df after shallow convert call ===")
    print(df)
    print("\n=== original dtypes after shallow convert call ===")
    print(df.dtypes)


if __name__ == "__main__":
    main()

