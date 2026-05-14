# 환경변수 로드 (.env 파일)
from dotenv import load_dotenv
from DATABASE.dbms.postgre import pg_manager

load_dotenv()

__all__ = ["pg_manager"]
