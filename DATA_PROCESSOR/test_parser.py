import io
from pathlib import Path

import pytest

from CUSTOMIZED.cust_excel_processor import ExcelProcessor
from DATA_PROCESSOR.edi_lotte import EdiLotte
from DATA_PROCESSOR.edi_silla import EdiSilla
from DATA_PROCESSOR.patch import fix_invalid_datetime_in_xlsx_bytes


_SCRIPT_DIR = Path(__file__).resolve().parent
EXCEL_PATH_LOTTE = _SCRIPT_DIR / "testdata" / "testdata_for_edi_lotte.xlsx"
EXCEL_PATH_SILLA = _SCRIPT_DIR / "testdata" / "testdata_for_edi_silla.xlsx"


def _load_flattened_excel(excel_path: str):
    """
    테스트와 수동 실행에서 공통으로 쓰는 헬퍼.
    """
    excel_processor = ExcelProcessor(excel_path, header=[0, 1])
    return excel_processor.flatten_columns().to_dataframe()


def _load_silla_excel(excel_path: Path | str):
    """신라 엑셀: patch.py로 20250417T000000 형식 수정 후 로드."""
    path = Path(excel_path)
    with open(path, "rb") as f:
        patched = fix_invalid_datetime_in_xlsx_bytes(f.read())
    excel_processor = ExcelProcessor(io.BytesIO(patched), header=[0, 1])
    return excel_processor.flatten_columns().to_dataframe()


@pytest.mark.skipif(not EXCEL_PATH_LOTTE.exists(), reason="롯데 테스트 데이터 파일 없음")
def test_edi_lotte_parse_not_empty():
    """
    - 엑셀 전처리 결과가 비어 있지 않은지
    - EdiLotte 파싱 결과가 비어 있지 않은지
    - 최소 한 개 이상의 컬럼이 생성되는지
    를 검증하는 기본 자동화 테스트.
    """
    df = _load_flattened_excel(str(EXCEL_PATH_LOTTE))

    edi_lotte_df = EdiLotte().set_original_data(df).parse()

    # 기본 검증
    assert not df.empty
    assert not edi_lotte_df.empty
    assert len(edi_lotte_df.columns) > 0


@pytest.mark.skipif(not EXCEL_PATH_SILLA.exists(), reason="신라 테스트 데이터 파일 없음")
def test_edi_silla_parse_not_empty():
    """
    - 엑셀 전처리 결과가 비어 있지 않은지
    - EdiSilla 파싱 결과가 비어 있지 않은지
    - 최소 한 개 이상의 컬럼이 생성되는지
    를 검증하는 기본 자동화 테스트.
    """
    df = _load_silla_excel(EXCEL_PATH_SILLA)

    edi_silla_df = EdiSilla().set_original_data(df).parse()

    # 기본 검증
    assert not df.empty
    assert not edi_silla_df.empty
    assert len(edi_silla_df.columns) > 0


if __name__ == "__main__":
    # 수동으로 돌려보고 싶을 때는 그대로 실행하면 샘플이 출력되도록 유지
    if EXCEL_PATH_LOTTE.exists():
        df_lotte = _load_flattened_excel(str(EXCEL_PATH_LOTTE))
        edi_lotte_df = EdiLotte().set_original_data(df_lotte).parse()
        print("=== Parsed EDI_Lotte head ===")
        print(edi_lotte_df.head())
        print("\n=== Parsed EDI_Lotte columns ===")
        for column in edi_lotte_df.columns:
            print(column)
    else:
        print(f"(EDI_Lotte 스킵: {EXCEL_PATH_LOTTE} 없음)")

    if EXCEL_PATH_SILLA.exists():
        df_silla = _load_silla_excel(EXCEL_PATH_SILLA)
        edi_silla_df = EdiSilla().set_original_data(df_silla).parse()
        print("\n=== Parsed EDI_Silla head ===")
        print(edi_silla_df.head())
        print("\n=== Parsed EDI_Silla columns ===")
        for column in edi_silla_df.columns:
            print(column)
    else:
        print(f"\n(EDI_Silla 스킵: {EXCEL_PATH_SILLA} 없음)")