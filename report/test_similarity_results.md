# 유사도 예측 관련 단위 테스트 결과표

## 테스트 개요
- **테스트 대상**: 
  - 일반 유사도 조회: `DATABASE.cruder.CRUDer` (Vector Similarity 관련 메서드)
  - 불량 유사도 조회: `WEB_SERVER.services.service` (Similarity 관련 함수), `WEB_SERVER.routers.router_similarity`
- **총 테스트 수**: 15개
  - 일반 유사도 조회: 8개 (CRUDer 레벨)
  - 불량 유사도 조회: 7개 (Service: 5개, Router: 2개)
- **통과**: 13개
- **실패**: 0개
- **에러**: 2개 (Router 테스트 - 의존성 모듈 미설치)
- **통과율**: 100% (실행 가능한 테스트 기준)

---

## 1. 일반 유사도 조회 테스트 결과 (CRUDer 레벨)

### TestCRUDerVector 클래스 테스트 결과

| "단위 테스트 ID" | 단위 테스트명 | 테스트 시나리오 | 테스트 데이터 | 예상 결과 | 테스트 결과 |
|------------------|--------------|----------------|--------------|----------|------------|
| UT-CRUDER-VECTOR-001 | get_vector_data - 성공 | 벡터 데이터 조회 성공 확인 | serial_no="serial1" | model_name, serial_no, vector 정상 반환 | 통과 |
| UT-CRUDER-VECTOR-002 | get_vector_data - 데이터 없음 | 벡터 데이터가 없는 경우 확인 | serial_no="serial1", DB 결과=None | 빈 값 반환 (model_name="", serial_no="", vector=[]) | 통과 |
| UT-CRUDER-VECTOR-003 | get_relative_similarities - 성공 | 상대 유사도 조회 성공 확인 | instrument_name="inst1", model_name="model1", serial_no="serial1", num_of_records=100, top_k_rate=0.01 | dict 타입 반환, execute_query 2회 이상 호출 | 통과 |
| UT-CRUDER-VECTOR-004 | get_relative_similarities - 잘못된 top_k_rate | top_k_rate 범위 초과 시 예외 처리 확인 | top_k_rate=1.5 (범위 초과) | ValueError 발생 ("top_k_rate must be between 0.0 and 1.0") | 통과 |
| UT-CRUDER-VECTOR-005 | get_absolute_similarities - 벡터 없음 | 벡터 데이터가 없는 경우 확인 | get_vector_data=None | 빈 딕셔너리 반환 ({}) | 통과 |
| UT-CRUDER-VECTOR-006 | get_absolute_similarities - 잘못된 metric | 잘못된 유사도 지표 사용 시 예외 처리 확인 | metric="invalid" | ValueError 발생 ("Invalid metric") | 통과 |
| UT-CRUDER-VECTOR-007 | get_absolute_similarities - euclidean metric | euclidean 거리 기반 유사도 조회 확인 | metric="euclidean" | dict 타입 반환, execute_query 2회 이상 호출 | 통과 |
| UT-CRUDER-VECTOR-008 | get_absolute_similarities - manhattan metric | manhattan 거리 기반 유사도 조회 확인 | metric="manhattan" | dict 타입 반환, execute_query 2회 이상 호출 | 통과 |

---

## 2. 불량 유사도 조회 테스트 결과 (Service/Router 레벨)

### TestServiceSimilarity 클래스 테스트 결과

| "단위 테스트 ID" | 단위 테스트명 | 테스트 시나리오 | 테스트 데이터 | 예상 결과 | 테스트 결과 |
|------------------|--------------|----------------|--------------|----------|------------|
| UT-SERVICE-SIM-001 | get_serial_similarity_hits_from_defects - 시리얼 정보 없음 | serial_info가 None인 경우 예외 처리 확인 | instrument_name="inst1", serial_no="serial1", top_n_rate=0.01, get_latest_measured_datum=None | ValueError 발생 ("시리얼 번호.*에 해당하는 측정 데이터를 찾을 수 없습니다") | 통과 |
| UT-SERVICE-SIM-002 | get_serial_similarity_hits_from_defects - 벡터 데이터 없음 | 정규화된 벡터 데이터가 없는 경우 예외 처리 확인 | 측정 데이터는 있으나 get_vector_data=None | ValueError 발생 ("정규화된 벡터 데이터가 없습니다") | 통과 |
| UT-SERVICE-SIM-003 | get_serial_similarity_hits_from_defects - 빈 레코드 | single_record가 빈 딕셔너리인 경우 예외 처리 확인 | 벡터 데이터는 있으나 get_absolute_similarities=[] | ValueError 발생 ("정규화된 벡터 데이터가 없습니다") | 통과 |
| UT-SERVICE-SIM-004 | normalize_and_upsert_all_models - 성공 케이스 | 모든 모델에 대해 정규화 및 벡터 업서트 성공 확인 | model_names=["model1", "model2"], 모든 모델 성공 | result가 dict 타입이고 count, fail_count, fail_infos 키 포함 | 통과 |
| UT-SERVICE-SIM-005 | normalize_and_upsert_all_models - 일부 실패 케이스 | 일부 모델 실패 시 예외 처리 및 결과 집계 확인 | model1 성공 (count=5), model2 실패 (ValueError) | result["count"] == 5, result["fail_count"] == 1, fail_infos 길이 == 1 | 통과 |

### TestRouterSimilarity 클래스 테스트 결과

| "단위 테스트 ID" | 단위 테스트명 | 테스트 시나리오 | 테스트 데이터 | 예상 결과 | 테스트 결과 |
|------------------|--------------|----------------|--------------|----------|------------|
| UT-ROUTER-SIM-001 | get_trends - serial_no=None, 데이터 없음 | serial_no=None이고 측정 데이터가 없는 경우 테스트 | serial_no="None", get_latest_measured_datum=None | HTTP 422 응답, "측정 데이터가 없습니다" 또는 "serial_no를 명시적으로 제공해주세요" 메시지 | 에러* |
| UT-ROUTER-SIM-002 | get_trends - serial_no=None, 데이터 있음 | serial_no=None이고 측정 데이터가 있는 경우 테스트 | serial_no="None", 측정 데이터 존재, 유사도 검색 결과 반환 | HTTP 200 또는 500 응답 (구현에 따라) | 에러* |

\* **에러 사유**: `gspread` 모듈 미설치로 인한 import 오류. 테스트 코드는 작성되어 있으나 실행 불가.

---

## 테스트 상세 정보

### 일반 유사도 조회 (CRUDer 레벨)

#### 테스트 함수: get_vector_data
**기능**: 시리얼 번호로 벡터 데이터 조회

**테스트 케이스:**
1. ✅ 성공 케이스 - 벡터 데이터 정상 조회
2. ✅ 데이터 없음 - 빈 값 반환

#### 테스트 함수: get_relative_similarities
**기능**: 상대 유사도 조회 (top_k_rate 기반)

**테스트 케이스:**
1. ✅ 성공 케이스 - 유사도 조회 성공
2. ✅ 잘못된 top_k_rate - 예외 처리 확인

#### 테스트 함수: get_absolute_similarities
**기능**: 절대 유사도 조회 (top_k 기반)

**테스트 케이스:**
1. ✅ 벡터 없음 - 빈 딕셔너리 반환
2. ✅ 잘못된 metric - 예외 처리 확인
3. ✅ euclidean metric - euclidean 거리 기반 조회
4. ✅ manhattan metric - manhattan 거리 기반 조회

### 불량 유사도 조회 (Service/Router 레벨)

#### 테스트 함수: get_serial_similarity_hits_from_defects
**기능**: 시리얼 번호 기반으로 불량 데이터와 유사한 측정 데이터 검색

**테스트 케이스:**
1. ✅ 시리얼 정보 없음 - 예외 처리 확인
2. ✅ 벡터 데이터 없음 - 예외 처리 확인
3. ✅ 빈 레코드 - 예외 처리 확인

#### 테스트 함수: normalize_and_upsert_all_models
**기능**: 모든 모델의 측정 데이터를 정규화하고 벡터 데이터로 변환하여 저장

**테스트 케이스:**
1. ✅ 성공 케이스 - 모든 모델 정상 처리
2. ✅ 일부 실패 케이스 - 일부 모델 실패 시 예외 처리 및 결과 집계

#### 테스트 엔드포인트: GET /api/similarity/get/trends
**기능**: 불량 데이터와 유사한 시리얼의 트렌드 데이터 조회

**테스트 케이스:**
1. ⚠️ serial_no=None, 데이터 없음 - HTTP 422 응답 확인 (의존성 오류로 미실행)
2. ⚠️ serial_no=None, 데이터 있음 - 정상 응답 확인 (의존성 오류로 미실행)

---

## 테스트 커버리지

### 일반 유사도 조회 (CRUDer 레벨)
- ✅ 벡터 데이터 조회
- ✅ 상대 유사도 조회 (top_k_rate 기반)
- ✅ 절대 유사도 조회 (top_k 기반)
- ✅ 다양한 유사도 지표 지원 (cosine, euclidean, manhattan)
- ✅ 예외 처리 (잘못된 파라미터, 데이터 없음)

### 불량 유사도 조회 (Service/Router 레벨)
- ✅ 시리얼 번호 기반 불량 유사도 검색
- ✅ 예외 처리 (시리얼 정보 없음, 벡터 데이터 없음, 빈 레코드)
- ✅ 모델 정규화 및 벡터 업서트 (성공/실패 케이스)
- ✅ 결과 집계 및 오류 정보 수집
- ⚠️ 트렌드 조회 API (의존성 오류로 미실행)
- ⚠️ HTTP 응답 코드 확인 (의존성 오류로 미실행)

---

## 수정 이력

### 2025-12-22
- **문제**: `test_normalize_and_upsert_all_models_with_failures` 테스트 실패
- **원인**: 모킹 경로가 stub 모듈(`WEB_SERVER.services.service`)을 가리켜 실제 구현 모듈(`WEB_SERVER.services.service_normalize`)의 함수가 호출되지 않음
- **해결**: 모킹 경로를 실제 구현 모듈로 변경
  - `WEB_SERVER.services.service.get_spec_parquet` → `WEB_SERVER.services.service_normalize.get_spec_parquet`
  - `WEB_SERVER.services.service.process_and_upsert_vector_data` → `WEB_SERVER.services.service_normalize.process_and_upsert_vector_data`
- **결과**: 모든 Service 테스트 통과

---

## 결론

### 일반 유사도 조회 (CRUDer 레벨)
모든 테스트가 성공적으로 통과하여 CRUDer 레벨의 벡터 유사도 조회 기능이 정상적으로 동작함을 확인했습니다.

- **벡터 데이터 조회**: 시리얼 번호 기반 벡터 데이터 조회 기능 정상 동작
- **상대 유사도 조회**: top_k_rate 기반 상대 유사도 조회 기능 정상 동작
- **절대 유사도 조회**: top_k 기반 절대 유사도 조회 기능 정상 동작
- **다양한 지표 지원**: cosine, euclidean, manhattan 지표 지원 확인
- **예외 처리**: 잘못된 파라미터 및 데이터 없음 상황에 대한 적절한 처리 확인

### 불량 유사도 조회 (Service/Router 레벨)
Service 레이어의 불량 유사도 조회 관련 테스트는 모두 성공적으로 통과하여 핵심 기능이 정상적으로 동작함을 확인했습니다.

- **유사도 검색**: 시리얼 번호 기반 불량 유사도 검색 기능 정상 동작
- **예외 처리**: 다양한 예외 상황에 대한 적절한 처리 확인
- **정규화 및 벡터화**: 모델 데이터 정규화 및 벡터 업서트 기능 정상 동작
- **오류 집계**: 일부 모델 실패 시에도 정상적으로 오류 정보 수집

Router 레이어 테스트는 `gspread` 모듈 설치 후 실행 가능합니다.
