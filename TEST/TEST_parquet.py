import os
from pathlib import Path

import duckdb
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from OPEN_SSH import ict_data_extractor

target_path = Path(r"C:\Users\윤대영\Desktop\업무\◈노바스이지\◆References\◆고객사 제공\5라인ict검사이력(-20250516)\DB92-05679A\2025\02\03\OK\06DB9205679ADVNAY1R0023_20250203080827.csv")
ict = ict_data_extractor.ICTDataExtractor()
ict.get(target_path)

output_dir = "silver/date=2025-06-24"
os.makedirs(output_dir, exist_ok=True)

i = ict.get_parquet_measured()
i['product_id'] = '제품ID'

i.to_parquet(
    "silver/date=2025-06-24/part-0000.parquet",
    engine="pyarrow",          # PyArrow 백엔드
    compression="snappy",      # Snappy(권장)·zstd·gzip 등
    row_group_size=64*1024*1024,     # 64 MB Row-Group
    write_statistics=True,     # min/max 통계 → push-down에 필수
    index=False                # 인덱스 컬럼 저장 안 함
)

# 연결
con = duckdb.connect()

# # Parquet 파일 읽기
# df = con.execute("SELECT * FROM 'silver/date=2025-06-24/part-0000.parquet'").df()

# # 또는
# df = con.read_parquet('silver/date=2025-06-24/part-0000.parquet')

filtered = con.execute("""
    SELECT * FROM 'silver/date=2025-06-24/*.parquet'
    WHERE measured_value = 91.59
""").df()

print(filtered)


filtered = con.execute("""SELECT step FROM 'silver/date=2025-06-24/*.parquet'""").df()

print(filtered)
print(type(filtered))



