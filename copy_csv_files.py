import os
import shutil
from pathlib import Path

def copy_csv_files():
    """
    D:\Report 폴더의 모든 CSV 파일을 D:\csv로 복사
    """
    # 소스 폴더와 대상 폴더 설정
    source_folder = Path("D:/Report")
    target_folder = Path("D:/csv")
    
    # 대상 폴더가 없으면 생성
    target_folder.mkdir(parents=True, exist_ok=True)
    
    # 소스 폴더가 존재하는지 확인
    if not source_folder.exists():
        print(f"❌ 소스 폴더가 존재하지 않습니다: {source_folder}")
        return
    
    # CSV 파일 찾기 (하위 폴더 포함)
    csv_files = list(source_folder.rglob("*.csv"))
    
    if not csv_files:
        print(f"❌ {source_folder}에 CSV 파일이 없습니다.")
        return
    
    print(f"📁 소스 폴더: {source_folder}")
    print(f"📁 대상 폴더: {target_folder}")
    print(f"📊 발견된 CSV 파일: {len(csv_files)}개")
    
    # 하위 폴더별 파일 수 표시
    folder_counts = {}
    for csv_file in csv_files:
        folder = csv_file.parent
        folder_counts[folder] = folder_counts.get(folder, 0) + 1
    
    print("\n📂 하위 폴더별 파일 수:")
    for folder, count in sorted(folder_counts.items()):
        print(f"   {folder}: {count}개")
    
    print("-" * 50)
    
    # 파일 복사
    success_count = 0
    error_count = 0
    
    for csv_file in csv_files:
        try:
            # 대상 파일 경로
            target_file = target_folder / csv_file.name
            
            # 파일 복사
            shutil.copy2(csv_file, target_file)
            print(f"✅ 복사 완료: {csv_file.name}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 복사 실패: {csv_file.name} - {str(e)}")
            error_count += 1
    
    print("-" * 50)
    print(f"📈 복사 결과:")
    print(f"   성공: {success_count}개")
    print(f"   실패: {error_count}개")
    print(f"   총 파일: {len(csv_files)}개")

if __name__ == "__main__":
    copy_csv_files()
