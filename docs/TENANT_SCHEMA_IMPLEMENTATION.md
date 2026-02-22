# 테넌트별 스키마 구현 과정 및 개선 사항

## 개요

이 문서는 테넌트별 스키마 구현 과정에서 **AI(Cursor)가 제안한 잘못된 접근 방식**과 **사용자(Yun Dae-young)가 수정한 올바른 접근 방식**을 비교하여 정리한 문서입니다.

---

## 1. AI의 잘못된 접근 방식들

### 1.1 AI의 잘못된 접근: 과도한 복잡성 (ContextVar와 인스턴스 변수 혼용)

#### ❌ AI가 제안한 코드
```python
from contextvars import ContextVar

# 현재 테넌트 ID를 저장하는 컨텍스트 변수
current_tenant_id: ContextVar[Optional[int]] = ContextVar('current_tenant_id', default=None)

class PGDBManager:
    def __init__(self, ...):
        self._current_tenant_id: Optional[int] = None  # 인스턴스 변수도 함께 사용
    
    async def __aenter__(self) -> AsyncSession:
        # 컨텍스트 변수와 인스턴스 변수 둘 다 확인
        tenant_id = current_tenant_id.get() or self._current_tenant_id
        if tenant_id:
            await self._set_schema(self.session, tenant_id)
        return self.session
    
    def set_tenant_context(self, tenant_id: Optional[int]) -> None:
        self._current_tenant_id = tenant_id
        if tenant_id:
            current_tenant_id.set(tenant_id)
        else:
            current_tenant_id.set(None)
```

#### 문제점
- **복잡성**: ContextVar와 인스턴스 변수를 동시에 사용하여 추적이 어려움
- **비동기 컨텍스트 문제**: 여러 인스턴스나 비동기 환경에서 예상치 못한 동작 가능
- **디버깅 어려움**: "어디서 스키마가 바뀌는지" 추적하기 어려움
- **불필요한 추상화**: 단순한 작업을 과도하게 복잡하게 만듦

---

### 1.2 AI의 잘못된 접근: 메서드 시그니처에 tenant_id 파라미터 추가

#### ❌ AI가 제안한 코드
```python
async def execute_query(
    self, 
    query: str | Executable, 
    params: dict | list[dict] | None = None, 
    tenant_id: Optional[int] = None  # 모든 메서드에 tenant_id 추가
):
    async with self.session_maker() as session:
        effective_tenant_id = tenant_id or current_tenant_id.get() or self._current_tenant_id
        if effective_tenant_id:
            await self._set_schema(session, effective_tenant_id)
        # ...

async def upsert_dataframe(
    self, 
    table: DeclarativeBase, 
    df: pd.DataFrame, 
    try_normalize: bool = True, 
    tenant_id: Optional[int] = None  # 여기도 추가
) -> int:
    # ...
```

#### 문제점
- **API 복잡성**: 모든 메서드에 `tenant_id` 파라미터가 필요
- **일관성 부족**: 일부 메서드만 tenant_id를 받으면 혼란스러움
- **호출부 복잡성**: Repository나 Service에서 매번 tenant_id를 전달해야 함
- **유지보수 어려움**: 메서드 시그니처가 계속 변경됨

---

### 1.3 AI의 잘못된 접근: 스키마 존재 확인을 개별 쿼리로 실행

#### ❌ AI가 제안한 코드
```python
# 모든 스키마 존재 여부 확인
for schema in schemas:
    if not await self._exists_schema(schema):  # 각각 쿼리 실행
        logger.error(f"Schema '{schema}' does not exist")
        raise ValueError(f"Schema '{schema}' does not exist")
```

#### 문제점
- **비효율적**: 스키마 개수만큼 쿼리 실행 (예: 3개 스키마 = 3번 쿼리)
- **네트워크 오버헤드**: 불필요한 반복 쿼리
- **확장성 문제**: 스키마가 많아질수록 성능 저하

---

### 1.4 AI의 잘못된 접근: 불필요한 begin() 사용

#### ❌ AI가 제안한 코드
```python
async def get_all_schemas(self) -> list[str]:
    # 단순 조회인데 begin() 사용
    async with self.async_engine.begin() as conn:
        result = await conn.execute(
            text("SELECT nspname FROM pg_namespace ORDER BY nspname")
        )
        schemas = [row[0] for row in result.fetchall()]
        return schemas
```

#### 문제점
- **불필요한 트랜잭션**: 단순 조회는 트랜잭션이 필요 없음
- **복잡성**: `begin()` 컨텍스트 관리가 불필요
- **일관성 부족**: 다른 메서드는 `execute_query`를 사용하는데 여기만 다름

---

### 1.5 AI의 잘못된 성능 우려

#### ❌ AI가 한 잘못된 설명
```
방법 2: get_all_schemas() 사용 (간단)
- 모든 스키마를 가져와서 확인 (간단하지만 비효율적일 수 있음)
```

#### 문제점
- **과도한 최적화 우려**: 수천 개 스키마 정도는 전혀 문제 없음
- **실제 성능 차이 미미**: 현실적인 스케일에서는 차이가 거의 없음
- **가독성 vs 성능**: 가독성을 희생할 필요가 없었음

---

## 2. 사용자(Yun Dae-young)가 수정한 올바른 접근 방식

### 2.1 ✅ 사용자(Yun Dae-young)의 개선: 명시적 스키마 설정 (`set_schema()` 메서드)

#### ✅ 사용자(Yun Dae-young)가 수정한 코드
```python
async def set_schema(self, schemas: list[str]) -> Self:
    """
    스키마 설정 (search_path 변경)
    
    Args:
        schemas: 설정할 스키마 이름 리스트 (예: ["tenant_123", "public"])
                순서대로 검색 경로에 추가됨
                
    Returns:
        Self (메서드 체이닝)
    """
    # 스키마 존재 여부 확인
    await self.exist_schemas(schemas, raise_error=True)
    
    # search_path 설정
    schema_list = ", ".join([f'"{s}"' for s in schemas])
    await self.execute_query(text(f"SET search_path TO {schema_list}"))
    
    self.schemas = schemas.copy()
    logger.info(f"Schemas set to: {schema_list}")
    return self
```

#### 개선 사항
- **명시적**: 스키마 설정이 한 곳에서 명확하게 이루어짐
- **단순함**: ContextVar나 복잡한 컨텍스트 관리 불필요
- **메서드 체이닝**: `return self`로 유연한 사용 가능
- **디버깅 용이**: 스키마 변경 지점이 명확함

---

### 2.2 ✅ 사용자(Yun Dae-young)의 개선: 재사용 가능한 검증 로직 (`exist_schemas()`)

#### ✅ 사용자(Yun Dae-young)가 수정한 코드
```python
async def exist_schemas(self, schemas: list[str], raise_error: bool = False) -> bool:
    """
    스키마 목록 존재 여부 확인
    
    Args:
        schemas: 존재 여부를 확인할 스키마 이름 리스트
        raise_error: True면 존재하지 않는 스키마가 있을 때 예외 발생
        
    Returns:
        True: 모든 스키마가 존재하는 경우
        False: 하나 이상의 스키마가 존재하지 않는 경우
    """
    if schemas:
        all_schemas: set[str] = set(await self.get_all_schemas())
        missing_schemas: set[str] = set(schemas) - all_schemas
        if missing_schemas:
            logger.error(f"Schemas do not exist: {', '.join(missing_schemas)}")
            if raise_error:
                raise ValueError(f"Schemas do not exist: {', '.join(missing_schemas)}")
            return False
        return True
    return False
```

#### 개선 사항
- **재사용성**: 다른 곳에서도 스키마 검증 가능
- **효율성**: 한 번의 쿼리로 모든 스키마 확인
- **유연성**: `raise_error` 옵션으로 에러 처리 방식 선택 가능
- **간단함**: `get_all_schemas()` 재사용으로 코드 중복 제거

---

### 2.3 ✅ 사용자(Yun Dae-young)의 개선: 간단한 조회 메서드 (`get_all_schemas()`)

#### ✅ 사용자(Yun Dae-young)가 수정한 코드
```python
async def get_all_schemas(self) -> list[str]:
    """
    DB에 등록된 모든 스키마 목록 조회
    
    Returns:
        스키마 이름 리스트
    """
    result = await self.execute_query(text("SELECT nspname FROM pg_namespace ORDER BY nspname"))
    schemas = [row[0] for row in result.fetchall()]
    return schemas
```

#### 개선 사항
- **단순함**: `begin()` 없이 `execute_query` 사용
- **일관성**: 다른 메서드들과 동일한 패턴
- **재사용성**: 여러 곳에서 활용 가능
- **명확성**: 단일 책임 원칙 준수

---

## 3. 최종 결과물 비교

### 3.1 사용 방법 비교

#### ❌ AI가 제안한 방식 (복잡함)
```python
# ContextVar 설정
current_tenant_id.set(123)

# 또는 인스턴스 변수 설정
db_manager.set_tenant_context(123)

# 쿼리 실행 (내부에서 자동으로 스키마 전환)
result = await db_manager.execute_query(query, tenant_id=123)
```

#### ✅ 사용자(Yun Dae-young)가 수정한 방식 (명확함)
```python
# 명시적으로 스키마 설정
await db_manager.set_schema(["tenant_123", "public"])

# 이후 쿼리는 평소처럼 실행
result = await db_manager.execute_query(query)
```

---

### 3.2 코드 복잡도 비교

| 항목 | ❌ AI의 방식 | ✅ 사용자(Yun Dae-young)의 방식 |
|------|----------|------------|
| 메서드 수 | 5+ (복잡한 컨텍스트 관리) | 3 (명확한 책임 분리) |
| 파라미터 | 모든 메서드에 tenant_id 추가 | set_schema만 스키마 파라미터 |
| 추적 가능성 | 어려움 (여러 곳에서 변경) | 쉬움 (한 곳에서 명시적 설정) |
| 디버깅 | 어려움 | 쉬움 |
| 유지보수 | 어려움 | 쉬움 |

---

### 3.3 성능 비교

| 작업 | ❌ AI의 방식 | ✅ 사용자(Yun Dae-young)의 방식 |
|------|----------|------------|
| 스키마 존재 확인 (3개) | 3번 쿼리 | 1번 쿼리 |
| 스키마 설정 | 매 쿼리마다 확인 | 한 번만 설정 |
| 메모리 사용 | ContextVar + 인스턴스 변수 | 인스턴스 변수만 |

---

## 4. 핵심 교훈 (AI가 배운 것)

### 4.1 과도한 추상화는 독이 될 수 있다
- **❌ AI의 문제**: ContextVar, 인스턴스 변수, 자동 스키마 전환 등 복잡한 추상화를 제안
- **✅ 사용자(Yun Dae-young)의 해결**: 명시적이고 단순한 API 설계로 수정

### 4.2 성능 우려는 실제 데이터로 판단해야 한다
- **❌ AI의 문제**: "이론적으로" 비효율적일 수 있다고 과도하게 걱정하며 `get_all_schemas()`를 비효율적이라고 잘못 설명
- **✅ 사용자(Yun Dae-young)의 지적**: 수천 개 스키마 정도는 전혀 문제 없음, 수백만 개가 되어야 고려할 문제
- **✅ 사용자(Yun Dae-young)의 해결**: 실용적인 판단으로 `get_all_schemas()` 사용

### 4.3 가독성과 단순성이 최고의 최적화다
- **❌ AI의 문제**: 복잡한 최적화로 코드가 읽기 어려워짐
- **✅ 사용자(Yun Dae-young)의 해결**: 간단하고 명확한 코드가 유지보수 비용을 크게 줄임

### 4.4 불필요한 트랜잭션은 피해야 한다
- **❌ AI의 문제**: 단순 조회에 `begin()` 사용
- **✅ 사용자(Yun Dae-young)의 지적**: `begin()` 안 써도 되지 않냐?
- **✅ 사용자(Yun Dae-young)의 해결**: `execute_query`로 일관성 유지

---

## 5. 최종 아키텍처

### 5.1 스키마 관리 흐름

```
1. 스키마 설정
   ↓
   await db_manager.set_schema(["tenant_123", "public"])
   ↓
   - exist_schemas()로 검증
   - SET search_path TO "tenant_123", "public" 실행
   - self.schemas에 저장
   
2. 쿼리 실행
   ↓
   await db_manager.execute_query(query)
   ↓
   - 이미 설정된 search_path 사용
   - 추가 설정 불필요
```

### 5.2 핵심 메서드

1. **`set_schema(schemas: list[str])`**: 스키마 설정 (명시적)
2. **`exist_schemas(schemas: list[str], raise_error: bool)`**: 스키마 검증 (재사용)
3. **`get_all_schemas()`**: 모든 스키마 조회 (단순)

---

## 6. 결론

### ❌ AI가 제안한 방식 (개선 전)
- 복잡한 컨텍스트 관리 (ContextVar + 인스턴스 변수)
- 모든 메서드에 tenant_id 파라미터 추가
- 개별 쿼리로 스키마 확인 (N번 쿼리)
- 불필요한 트랜잭션 (`begin()` 사용)
- 과도한 성능 우려 (이론적 최적화에 집착)

### ✅ 사용자(Yun Dae-young)가 수정한 방식 (개선 후)
- 명시적이고 단순한 API (`set_schema()` 한 번 호출)
- 스키마 설정은 한 곳에서 (명확한 책임 분리)
- 효율적인 일괄 검증 (`get_all_schemas()` 재사용)
- 일관된 쿼리 실행 패턴 (`execute_query` 사용)
- 실용적인 성능 판단 (수천 개는 문제 없음)

**결과: 사용자(Yun Dae-young)의 개선으로 코드가 더 읽기 쉽고, 유지보수하기 쉽고, 디버깅하기 쉬워졌습니다.**

---

## 7. AI의 반성

이번 구현 과정에서 AI는 다음과 같은 실수를 했습니다:

1. **과도한 추상화**: ContextVar와 인스턴스 변수를 혼용하여 복잡성만 증가시킴
2. **불필요한 파라미터**: 모든 메서드에 tenant_id를 추가하여 API를 복잡하게 만듦
3. **비효율적인 쿼리**: 스키마 확인을 개별 쿼리로 실행
4. **불필요한 트랜잭션**: 단순 조회에 begin() 사용
5. **잘못된 성능 우려**: 이론적 최적화에 집착하여 실용성을 간과

**사용자(Yun Dae-young)의 피드백과 수정을 통해 올바른 방향으로 개선되었습니다.**

---

**작성일**: 2026.02.19  
**작성자**: Cursor AI  
**수정 및 개선**: Yun Dae-young  
**연락처**: Dreamer.Dy.Yun@Gmail.com
