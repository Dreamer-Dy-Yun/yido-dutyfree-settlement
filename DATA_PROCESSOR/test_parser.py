from CUSTOMIZED.cust_excel_processor import ExcelProcessor
from DATA_PROCESSOR.edi_lotte import EdiLotte


EXCEL_PATH_LOTTE = r"C:\TEST\YIDO.DUTYFREE\DATA_PROCESSOR\testdata\testdata_for_edi_lotte.xlsx"


def _load_flattened_excel(excel_path: str):
    """
    테스트와 수동 실행에서 공통으로 쓰는 헬퍼.
    """
    excel_processor = ExcelProcessor(excel_path, header=[0, 1])
    return excel_processor.flatten_columns().to_dataframe()


def test_edi_lotte_parse_not_empty():
    """
    - 엑셀 전처리 결과가 비어 있지 않은지
    - EdiLotte 파싱 결과가 비어 있지 않은지
    - 최소 한 개 이상의 컬럼이 생성되는지
    를 검증하는 기본 자동화 테스트.
    """
    df = _load_flattened_excel(EXCEL_PATH_LOTTE)

    edi_lotte_df = EdiLotte().set_original_data(df).parse()

    # 기본 검증
    assert not df.empty
    assert not edi_lotte_df.empty
    assert len(edi_lotte_df.columns) > 0


if __name__ == "__main__":
    # 수동으로 돌려보고 싶을 때는 그대로 실행하면 샘플이 출력되도록 유지
    df = _load_flattened_excel(EXCEL_PATH_LOTTE)
    edi_lotte_df = EdiLotte().set_original_data(df).parse()

    print("=== Parsed EDI_Lotte head ===")
    print(edi_lotte_df.head())

    print("\n=== Parsed columns ===")
    for column in edi_lotte_df.columns:
        print(column)