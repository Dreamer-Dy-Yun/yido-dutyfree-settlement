import time
import pandas as pd
from pathlib import Path
from datetime import datetime


def create_csv_files(
    max_count: int,
    prefix: str = "test",
    output_path: str | Path = ".",
    interval_seconds: float = 1.0
) -> None:
    """
    매 interval_seconds마다 CSV 파일을 생성합니다.
    
    Args:
        max_count: 생성할 파일의 최대 개수 (상한)
        prefix: 파일명 접두사 (기본값: "test")
        output_path: 파일을 저장할 경로 (기본값: 현재 디렉토리)
        interval_seconds: 파일 생성 간격 (초, 기본값: 1.0)
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 출력 경로: {output_path.absolute()}")
    print(f"🔢 최대 생성 개수: {max_count}")
    print(f"⏱️  생성 간격: {interval_seconds}초")
    print(f"🏷️  파일명 접두사: {prefix}")
    print("-" * 50)
    
    for i in range(1, max_count + 1):
        # 파일명: prefix + 연월일시분초.csv
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{prefix}{timestamp}.csv"
        filepath = output_path / filename
        
        # 샘플 데이터 생성 (예시)
        df = pd.DataFrame({
            "id": [i],
            "timestamp": [datetime.now().isoformat()],
            "value": [i * 10],
            "status": ["created"]
        })
        
        # CSV 파일 저장
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        print(f"✅ [{i}/{max_count}] 생성 완료: {filename}")
        
        # 마지막 파일이 아니면 대기
        if i < max_count:
            time.sleep(interval_seconds)
    
    print("-" * 50)
    print(f"✨ 총 {max_count}개의 파일 생성 완료!")


if __name__ == "__main__":
    # 사용 예시
    create_csv_files(
        max_count=1000,           # 10개 파일 생성
        prefix="(test)_0호기_",    # 파일명: test_file_1.csv, test_file_2.csv, ...
        output_path=rf"C:\Users\USER\Desktop\0호기",  # ./test_csv 폴더에 저장
        interval_seconds=1.0     # 1초마다 생성
    )

    create_csv_files(
        max_count=1000,           # 10개 파일 생성
        prefix="(test)_1호기_",    # 파일명: test_file_1.csv, test_file_2.csv, ...
        output_path=rf"C:\Users\USER\Desktop\1호기",  # ./test_csv 폴더에 저장
        interval_seconds=1.0     # 1초마다 생성
    )