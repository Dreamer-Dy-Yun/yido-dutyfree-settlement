# SpecAnalyzer 단위 테스트 결과표

## 테스트 개요
- **테스트 대상**: `ANALYZER.spec_analyzer.SpecAnalyzer`, `AnalyzedFileExporter`
- **총 테스트 수**: 17개
- **통과**: 17개
- **실패**: 0개
- **통과율**: 100%
- **실행 시간**: 1.32초

---

## TestSpecAnalyzer 클래스 테스트 결과

| "단위 테스트 ID" | 단위 테스트명 | 테스트 시나리오 | 테스트 데이터 | 예상 결과 | 테스트 결과 |
|------------------|--------------|----------------|--------------|----------|------------|
| UT-ANALYZER-SPEC-001 | SpecAnalyzer 초기화 | SpecAnalyzer 객체 생성 시 필드 초기화 확인 | spec DataFrame (3개 행), resolution=100 | spec, resolution, list_spec 필드가 정상 초기화되고 list_spec 길이가 3 | 통과 |
| UT-ANALYZER-SPEC-002 | run() 메서드 실행 | run() 호출 시 리스트 필드 생성 확인 | spec DataFrame (3개 행), resolution=100 | list_ucv, list_lcv, list_usl, list_lsl, list_part_name이 생성되고 길이가 3 | 통과 |
| UT-ANALYZER-SPEC-003 | Spec 양자화 | quantize() 호출 시 Spec 값 양자화 확인 | spec DataFrame (3개 행), resolution=100 | spec_quantized, usl_quantized, lsl_quantized가 생성되고 길이가 3 | 통과 |
| UT-ANALYZER-SPEC-004 | analyze() 메서드 실행 | analyze() 호출 시 분석 데이터 생성 확인 | spec DataFrame, sample_data (5행 3열), resolution=100 | data_original, data_quantized, pmf, list_mu, list_sigma가 생성되고 반환값이 analyzer 객체 | 통과 |
| UT-ANALYZER-SPEC-005 | analyze() 차원 불일치 예외 | spec 행 수와 data 열 수 불일치 시 예외 발생 확인 | spec DataFrame (3행), wrong_data (1행 2열) | ValueError 발생 ("spec rows must match data columns") | 통과 |
| UT-ANALYZER-SPEC-006 | PMF 계산 | compute_pmf() 호출 시 PMF 행렬 생성 확인 | spec DataFrame, sample_data (5행 3열), resolution=100 | pmf.shape == (3, 100), 모든 값이 0 이상 1 이하 | 통과 |
| UT-ANALYZER-SPEC-007 | CPK 계산 | compute_cpk() 호출 시 CPK 값 계산 확인 | spec DataFrame, sample_data (5행 3열), resolution=100 | list_mu, list_sigma, list_cpk, list_type_cpk이 생성되고 길이가 3 | 통과 |
| UT-ANALYZER-SPEC-008 | 검사 결과 카운트 | count_inspection_outcomes() 호출 시 검사 결과 카운트 확인 | spec DataFrame, sample_data (5행 3열), resolution=100 | list_exceeded_usl, list_exceeded_lsl, list_exceeded_spec_total, list_between_spec_total이 생성되고 길이가 3 | 통과 |
| UT-ANALYZER-SPEC-009 | 다른 resolution 값 | 다른 resolution 값으로 초기화 시 정상 동작 확인 | spec DataFrame, resolution=200 | analyzer.resolution == 200 | 통과 |

---

## TestAnalyzedFileExporter 클래스 테스트 결과

| "단위 테스트 ID" | 단위 테스트명 | 테스트 시나리오 | 테스트 데이터 | 예상 결과 | 테스트 결과 |
|------------------|--------------|----------------|--------------|----------|------------|
| UT-ANALYZER-EXPORT-001 | AnalyzedFileExporter 초기화 | AnalyzedFileExporter 객체 생성 시 필드 초기화 확인 | sample_analyzer, model="test_model" | model, sa 필드가 정상 초기화되고 file_name_without_extension이 빈 문자열 | 통과 |
| UT-ANALYZER-EXPORT-002 | 파일명 설정 | set_file_name_without_extension() 호출 시 파일명 생성 확인 | query_from=2025-01-01, query_to=2025-01-31, execution_time=2025-01-15 10:00:00 | 파일명에 model, 날짜 정보가 포함되고 반환값이 file_name_without_extension과 동일 | 통과 |
| UT-ANALYZER-EXPORT-003 | 메타데이터 직렬화 | serialized_meta_data() 호출 시 메타데이터 직렬화 확인 | sample_analyzer | list 타입, 길이 2, 각 요소에 specInfo, chartSpecLine 포함, 첫 번째 요소의 idx=1, partName="part1" | 통과 |
| UT-ANALYZER-EXPORT-004 | PMF 데이터 직렬화 | serialized_pmf_data() 호출 시 PMF 데이터 직렬화 확인 | sample_analyzer | list 타입, 길이 2, 각 요소에 data, judgementInfo, cpkInfo 포함, data는 list 타입 | 통과 |
| UT-ANALYZER-EXPORT-005 | 트렌드 데이터 직렬화 | serialized_trend_data() 호출 시 트렌드 데이터 직렬화 확인 | sample_analyzer | dict 타입, 키 "1" 또는 1 존재, navigationIdx 포함 | 통과 |
| UT-ANALYZER-EXPORT-006 | Zero PMF 데이터 직렬화 | serialized_zero_pmf_data() 호출 시 Zero PMF 데이터 직렬화 확인 | sample_analyzer | list 타입, 길이 2, 첫 번째 요소의 judgementInfo.ok.total == 0 | 통과 |
| UT-ANALYZER-EXPORT-007 | 파일명 미설정 예외 | 파일명 미설정 상태에서 to_json_file() 호출 시 예외 발생 확인 | file_name_without_extension 미설정 상태 | ValueError 발생 ("file_name_without_extension is not set") | 통과 |
| UT-ANALYZER-EXPORT-008 | JSON 파일 생성 | to_json_file() 호출 시 JSON 파일 생성 확인 | 파일명 설정 후, test_data={"test": "data"}, tempdir 사용 | JSON 파일 1개 생성, 파일명에 "(meta)" 포함 | 통과 |

---

## 테스트 상세 정보

### 테스트 데이터 (sample_spec)
```python
DataFrame({
    "index": [1, 2, 3],
    "part_name": ["part1", "part2", "part3"],
    "spec": [500.0, 600.0, 700.0],
    "unit": ["ohm", "ohm", "ohm"],
    "ucv": [800.0, 900.0, 1000.0],
    "lcv": [200.0, 300.0, 400.0],
    "usl": [750.0, 850.0, 950.0],
    "lsl": [250.0, 350.0, 450.0],
    "reverse_tolerance": [False, False, False],
    "skip": [False, False, False]
})
```

### 테스트 데이터 (sample_data)
```python
[
    [500.0, 600.0, 700.0],
    [510.0, 610.0, 710.0],
    [490.0, 590.0, 690.0],
    [520.0, 620.0, 720.0],
    [480.0, 580.0, 680.0],
]
```

---

## 테스트 커버리지

### SpecAnalyzer 클래스
- ✅ 초기화 및 필드 설정
- ✅ Spec 양자화
- ✅ 데이터 분석 (analyze)
- ✅ PMF (Probability Mass Function) 계산
- ✅ CPK (Process Capability Index) 계산
- ✅ 검사 결과 카운트
- ✅ 차원 불일치 예외 처리
- ✅ 다양한 resolution 값 지원

### AnalyzedFileExporter 클래스
- ✅ 초기화 및 필드 설정
- ✅ 파일명 생성
- ✅ 메타데이터 직렬화
- ✅ PMF 데이터 직렬화
- ✅ 트렌드 데이터 직렬화
- ✅ Zero PMF 데이터 직렬화
- ✅ JSON 파일 생성
- ✅ 파일명 미설정 예외 처리

---

## 결론

모든 테스트가 성공적으로 통과하여 `SpecAnalyzer`와 `AnalyzedFileExporter` 클래스의 핵심 기능이 정상적으로 동작함을 확인했습니다.

- **초기화**: 모든 필드가 올바르게 초기화됨
- **데이터 분석**: 측정 데이터 분석 기능 정상 동작
- **통계 계산**: PMF, CPK 계산 정상 동작
- **데이터 직렬화**: 모든 직렬화 메서드 정상 동작
- **예외 처리**: 예외 상황에 대한 적절한 처리 확인
- **파일 생성**: JSON 파일 생성 기능 정상 동작

