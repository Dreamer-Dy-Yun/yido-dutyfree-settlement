import os

# Docker run 명령어 실행
os.system("""
docker run --name pgvector-test \
  -e POSTGRES_PASSWORD=123!@#qwe \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
""")