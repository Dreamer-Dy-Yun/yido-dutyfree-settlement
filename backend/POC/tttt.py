import os
import oracledb

HOST = "222.234.221.118"
PORT = 1521
SID  = "ORAEDS"  # 화면에 보인 마지막 토큰
USER = "HANA"
PWD  = "HANA"

SQL = """
SELECT T.ROWID AS RowId, T.*
FROM UBI08_SHANA."WMS주문" T
WHERE 주문KEY = :order_key
"""

def main():
    # 1) Instant Client 경로 (본인 PC 경로로 수정)
    oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_13")

    dsn = oracledb.makedsn(HOST, PORT, sid=SID)

    conn = None
    cur = None
    try:
        conn = oracledb.connect(user=USER, password=PWD, dsn=dsn)
        cur = conn.cursor()
        cur.execute(SQL, {"order_key": "20120710M01150100130001"})
        row = cur.fetchone()

        if row is None:
            print("✅ Thick 연결/쿼리 성공. 결과 0건.")
        else:
            print("✅ Thick 연결/쿼리 성공. 첫 행 수신 OK.")
            print("첫 행:", row)

    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    main()