import pandas as pd
import json
from pathlib import Path

def save_df_to_json(df: pd.DataFrame, output_path: str | Path = "df_output.json"):
    """
    DataFrame을 JSON 파일로 저장
    
    Args:
        df: 저장할 DataFrame
        output_path: 출력 파일 경로 (기본값: df_output.json)
    """
    output_path = Path(output_path)
    
    # DataFrame을 딕셔너리로 변환
    # orient='records'는 각 행을 딕셔너리로 변환
    data = df.to_dict(orient='records')
    
    # JSON 파일로 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ DataFrame이 JSON 파일로 저장되었습니다: {output_path}")
    print(f"   - 행 수: {len(df)}")
    print(f"   - 컬럼: {list(df.columns)}")
    
    return output_path

# 사용 예시:
# df = ... (디버거에서 확인한 DataFrame)
# save_df_to_json(df, "debug_df.json")

