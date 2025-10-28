from DATABASE import pg_manager, models

db_manager = pg_manager.PGDBManager(
    models.BaseModel,
    db_name="novas_ez",
    user="admin",
    password="123!@#qwe",
    host="localhost",
    port=5432
)


# Sqlalchemy 에서 지원하지 않으므로 직접 쿼리 실행
# TODO : 언젠가 공통 모듈로 변경 예정
def apply_postgres_vector_scale_index(db_manager: pg_manager.PGDBManager):
    db_manager.execute_query("CREATE EXTENSION IF NOT EXISTS vectorscale;")
    db_manager.execute_query("""
        CREATE INDEX IF NOT EXISTS ix_normalized_vec_diskann_cos ON normalized USING diskann (vector_visual_normed vector_cosine_ops);
        CREATE INDEX IF NOT EXISTS ix_normalized_vec_diskann_l2 ON normalized USING diskann (vector_visual_normed vector_l2_ops);
        CREATE INDEX IF NOT EXISTS ix_normalized_vec_diskann_ip ON normalized USING diskann (vector_visual_normed vector_ip_ops);
    """)

apply_postgres_vector_scale_index(db_manager)