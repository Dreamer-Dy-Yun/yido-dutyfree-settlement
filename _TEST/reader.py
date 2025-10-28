import pandas as pd
from io import StringIO

# CSV 파일 경로 지정
csv_path = r"C:\Users\윤대영\Desktop\업무\◈노바스이지\◆References\◆고객사 제공\5라인ict검사이력(-20250516)\DB92-05679A\2025\02\03\OK\06DB9205679ADVNAY1R0023_20250203080827.csv"  # ← 여기에 실제 파일 경로 입력

with open(csv_path, 'r') as f:
    lines = f.readlines()


do_read = False
csv_records = []
for line in lines:
    SN = ""
    DT = ""
    if "Serial No." in line:
        SN = line.split(",")[1].strip()
        print(SN)
    if "Date" in line:
        DT = line.split(",")[1].strip()
        print(DT)
    if "Step" in line:
        do_read = True
    if do_read:
        if not "----------" in line:
            csv_records.append(line.strip())
            # print(line.strip())


df = pd.read_csv(StringIO("\n".join(csv_records)))

print(df)
