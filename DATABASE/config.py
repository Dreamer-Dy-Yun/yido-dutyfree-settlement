import os
from DATABASE import pg_manager, models
from DATABASE.cruder import CRUDer

db_manager = pg_manager.PGDBManager(
    models.BaseModel,
    db_name=os.getenv("DB_NAME", "novas_ez"),
    user=os.getenv("DB_USER", "admin"),
    password=os.getenv("DB_PASSWORD", "123!@#qwe"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432"))
)

cruder = CRUDer(db_manager)

# Sqlalchemy 에서 지원하지 않으므로 직접 쿼리 실행
# TODO : 언젠가 공통 모듈로 변경 예정
async def apply_postgres_vector_scale_index(db_manager: pg_manager.PGDBManager):
    await db_manager.execute_query("CREATE EXTENSION IF NOT EXISTS vectorscale;")
    await db_manager.execute_query(
        "CREATE INDEX IF NOT EXISTS ix_normalized_vec_diskann_cos ON normalized USING diskann (vector_visual_normed vector_cosine_ops);"
    )
    await db_manager.execute_query(
        "CREATE INDEX IF NOT EXISTS ix_normalized_vec_diskann_l2 ON normalized USING diskann (vector_visual_normed vector_l2_ops);"
    )
    await db_manager.execute_query(
        "CREATE INDEX IF NOT EXISTS ix_normalized_vec_diskann_ip ON normalized USING diskann (vector_visual_normed vector_ip_ops);"
    )

# 주의: import 시점에 실행하지 않음. 앱 시작 시점에 await로 호출할 것.