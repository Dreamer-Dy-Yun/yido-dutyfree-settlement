"""
JSON 파일에서 데이터를 읽어서 테이블에 UPSERT하는 스크립트
"""
import json
import asyncio
import pandas as pd
from pathlib import Path
from datetime import datetime
from DATABASE.config import db_manager, cruder
from DATABASE import models
from data_archiver import DataArchiver
from OPEN_SSH.ict_data_extractor import ICTDataExtractor

async def upsert_from_json(json_file_path: str | Path):
    """
    JSON 파일을 읽어서 on_spec을 거쳐서 UPSERT
    
    Args:
        json_file_path: JSON 파일 경로
    """
    json_file_path = Path(json_file_path)
    
    if not json_file_path.exists():
        raise FileNotFoundError(f"JSON 파일이 존재하지 않습니다: {json_file_path}")
    
    # JSON 파일 읽기
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📄 JSON 파일 읽기 완료: {json_file_path}")
    print(f"   - 데이터 개수: {len(data)}")
    
    # DataArchiver 인스턴스 생성
    data_archiver = DataArchiver(db_manager)
    
    # 각 데이터 항목에 대해 처리
    for item in data:
        print(f"\n📊 처리 중: {item.get('model_name', 'N/A')}")
        
        # JSON 데이터를 ICTDataExtractor 객체로 변환
        ict_data = ICTDataExtractor()
        ict_data.measured_by = item.get('instrument_name', '')
        ict_data.model_name = item.get('model_name', '')
        ict_data.measured_points = item.get('measured_points', 0)
        ict_data.adj_val_infinity = item.get('adj_val_infinity', 0.0)
        ict_data.adj_val_extreme = item.get('adj_val_extreme', 0.0)
        
        # updated_at을 datetime으로 변환
        updated_at_str = item.get('updated_at', '')
        if updated_at_str:
            ict_data.measured_at = pd.to_datetime(updated_at_str).to_pydatetime()
        else:
            ict_data.measured_at = datetime.now()
        
        # path_sub_datafile과 hashed_datafile 처리
        datafile_subpath = Path(item.get('path_sub_datafile', ''))
        
        # hashed_datafile을 bytes로 변환
        hashed_datafile_str = item.get('hashed_datafile', '')
        if isinstance(hashed_datafile_str, str):
            if hashed_datafile_str.startswith("b'") or hashed_datafile_str.startswith('b"'):
                datafile_hash = eval(hashed_datafile_str)
            else:
                datafile_hash = hashed_datafile_str.encode()
        else:
            datafile_hash = hashed_datafile_str
        
        # on_spec을 통해 UPSERT
        try:
            result_df = await data_archiver.on_spec(ict_data, datafile_subpath, datafile_hash)
            print(f"✅ UPSERT 완료: {len(result_df)}개 행 처리됨")
        except Exception as e:
            print(f"❌ UPSERT 실패: {e}")
            raise

async def main():
    """메인 함수"""
    json_file = "debug_df.json"
    
    await upsert_from_json(json_file)
    print("\n✅ 모든 작업 완료!")

if __name__ == "__main__":
    asyncio.run(main())

