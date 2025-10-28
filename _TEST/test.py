from cust_logger import logger
import db_manager

# 접속 정보 설정
DB_NAME = 'postgres'
DB_USER = 'postgres'
DB_PASSWORD = '123!@#qwe'  # ← 이스케이프 제거
DB_HOST = 'localhost'
DB_PORT = '5432'

db = db_manager.DatabaseManager(DB_NAME,DB_USER,DB_PASSWORD,DB_HOST,DB_PORT)

