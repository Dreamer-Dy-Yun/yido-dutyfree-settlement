import pandas as pd

from LLM.dto import LLMResponse, LLMUsage
from PROCESSOR_LLM_RESULT.yido_parser import YidoParser


def test_yido_parser_normalizes_receipts_passports_and_usage(monkeypatch):
    monkeypatch.setattr("PROCESSOR_LLM_RESULT.yido_parser.time.time", lambda: 110.0)
    parser = YidoParser().add_uuid_batch("batch-001")
    response = LLMResponse(
        model="ocr-model",
        start_time=100.0,
        usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        content={
            "receipts": {
                "list": [
                    {
                        "dutyfree_company": " lotte ",
                        "group_no": " G1 ",
                        "receipt_no": " R-001 ",
                        "country_code": " kor ",
                        "passport_no": " p123 ",
                        "purchaser": " hong gil dong ",
                        "coordinate": {"x": 1.0, "y": 2.0},
                    }
                ]
            },
            "passports": {
                "list": [
                    {
                        "country_code": " KOR ",
                        "passport_no": " P123 ",
                        "name": " Hong ",
                        "gender": " M ",
                        "coordinate": {"x": 3.0, "y": 4.0},
                    }
                ]
            },
        },
    )

    parser.run(response)

    receipt = parser.df_receipt.iloc[0].to_dict()
    assert receipt["dutyfree_company"] == "LOTTE"
    assert receipt["group_no"] == "G1"
    assert receipt["receipt_no"] == "R-001"
    assert receipt["country_code"] == "KOR"
    assert receipt["passport_no"] == "P123"
    assert receipt["purchaser"] == "HONG GIL DONG"
    assert receipt["uuid_batch"] == "batch-001"
    assert len(receipt["hash_ocr_result"]) == 64
    assert len(receipt["uuid_record"]) == 32

    passport = parser.df_passport.iloc[0].to_dict()
    assert passport["country_code"] == "KOR"
    assert passport["passport_no"] == "P123"
    assert passport["name"] == "Hong"
    assert passport["uuid_batch"] == "batch-001"
    assert len(passport["hash_ocr_result"]) == 64

    usage = parser.df_usage.iloc[0].to_dict()
    assert usage["model"] == "ocr-model"
    assert usage["prompt_tokens"] == 10
    assert usage["completion_tokens"] == 20
    assert usage["total_tokens"] == 30
    assert usage["elapsed_time"] == 10.0


def test_yido_parser_empty_response_creates_empty_dataframes():
    parser = YidoParser()
    parser.run(LLMResponse(content={"receipts": {"list": []}, "passports": {"list": []}}))

    assert parser.df_receipt.empty
    assert parser.df_passport.empty
    assert parser.df_usage is None or parser.df_usage.empty


def test_yido_parser_add_hashed_image_backfills_existing_rows(tmp_path):
    image_path = tmp_path / "receipt.png"
    image_path.write_bytes(b"fake-image")
    parser = YidoParser()
    parser._df_receipt = pd.DataFrame([{"receipt_no": "R1"}])
    parser._df_passport = pd.DataFrame([{"passport_no": "P1"}])

    parser.add_hashed_image(image_path)

    assert len(parser.hashed_image) == 64
    assert parser.df_receipt.loc[0, "hash_img"] == parser.hashed_image
    assert parser.df_passport.loc[0, "hash_img"] == parser.hashed_image
