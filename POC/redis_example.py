"""
Redis 사용 예제 (동기 방식)
- redis 서버가 localhost:6379 에 떠 있어야 함.
- 실행: python -m POC.redis_example (프로젝트 루트에서)
"""
import os

import redis
from dotenv import load_dotenv

load_dotenv()

# 연결 설정 (환경변수 또는 기본값)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_client() -> redis.Redis:
    return redis.from_url(REDIS_URL, decode_responses=True)


def example_string(client: redis.Redis) -> None:
    """문자열 get/set"""
    key = "poc:greeting"
    client.set(key, "hello redis")
    val = client.get(key)
    print(f"  [string] set/get: {val}")
    client.delete(key)


def example_hash(client: redis.Redis) -> None:
    """해시 (객체처럼 필드-값)"""
    key = "poc:user:1"
    client.hset(key, mapping={"name": "홍길동", "age": "30", "city": "Seoul"})
    name = client.hget(key, "name")
    full = client.hgetall(key)
    print(f"  [hash] hget name: {name}, hgetall: {full}")
    client.delete(key)


def example_list(client: redis.Redis) -> None:
    """리스트 (큐/스택)"""
    key = "poc:queue"
    client.rpush(key, "a", "b", "c")
    first = client.lpop(key)
    remaining = client.lrange(key, 0, -1)
    print(f"  [list] lpop: {first}, lrange: {remaining}")
    client.delete(key)


def example_set(client: redis.Redis) -> None:
    """집합 (중복 없음)"""
    key = "poc:tags"
    client.sadd(key, "python", "redis", "cache")
    members = client.smembers(key)
    print(f"  [set] smembers: {members}")
    client.delete(key)


def example_ttl(client: redis.Redis) -> None:
    """만료 시간 (TTL)"""
    key = "poc:session:abc"
    client.setex(key, 60, "session_data")  # 60초 후 삭제
    ttl = client.ttl(key)
    print(f"  [ttl] setex 60s, ttl={ttl}")
    client.delete(key)


def example_pipeline(client: redis.Redis) -> None:
    """파이프라인 (여러 명령 한 번에)"""
    pipe = client.pipeline()
    pipe.set("poc:p1", "v1")
    pipe.set("poc:p2", "v2")
    pipe.get("poc:p1")
    pipe.get("poc:p2")
    results = pipe.execute()
    print(f"  [pipeline] execute results: {results}")
    client.delete("poc:p1")
    client.delete("poc:p2")


def run_examples() -> None:
    print("Redis 예제 실행 (REDIS_URL=%s)\n" % REDIS_URL)
    try:
        client = get_client()
        client.ping()
    except redis.ConnectionError as e:
        print("Redis 연결 실패. redis 서버를 띄운 뒤 다시 시도하세요.")
        print("  예: docker run -d -p 6379:6379 redis")
        print("  오류:", e)
        return

    example_string(client)
    example_hash(client)
    example_list(client)
    example_set(client)
    example_ttl(client)
    example_pipeline(client)
    print("\n예제 완료.")


if __name__ == "__main__":
    run_examples()
