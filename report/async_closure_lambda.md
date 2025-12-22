### 파이썬 비동기 루프 + lambda에서 마지막 `fr`만 실행되는 이유

---

### 1. 문제 코드 패턴

```python
for row in df_instrument.itertuples(index=False):
    instrument_name: str = row.name
    fr = fr_dict[instrument_name]

    fr.set_download_batch_size(ICTRetrieveRunner._DOWNLOAD_BATCH_SIZE)
    fr.set_fetch_list_limit(ICTRetrieveRunner._FETCH_LIST_LIMIT)

    retrier = Retrier.retry(
        lambda: fr.run(),
        on_retry=lambda: fr.connect_to_instrument(),
    )
    tasks.append(asyncio.create_task(retrier))
```

- 의도: 각 장비(MI-01, MI-02, …)에 대해 **자기 전용 `fr.run()`** 을 비동기로 실행하고 싶음.
- 실제 동작: **모든 lambda가 마지막 반복에서의 `fr`(예: MI-02)만 참조**해서  
  MI-01용 `run()`은 아예 호출되지 않는 문제가 발생.

---

### 2. 원인: 파이썬 클로저의 지연 바인딩(late binding)

파이썬에서 lambda(혹은 내부 함수)는 변수의 **“값”이 아니라 “이름”** 을 캡처한다.

- `lambda: fr.run()` 안에는 **“지금 시점의 fr 값”이 저장되는 게 아니라**,
  - “나중에 실행할 때 `fr`라는 이름을 현재 스코프에서 찾아 써라” 는 **규칙**이 저장된다.
- 루프가 모두 끝난 후, `fr` 변수는 **마지막 반복에서 대입된 객체**(예: MI-02의 `FileRetriever`)를 가리키고 있다.
- 따라서 나중에 모든 lambda를 실행하면:
  - `fr` 이름을 해석할 때마다 **항상 마지막 값(예: MI-02)** 만 사용하게 된다.

이 패턴을 **지연 바인딩(late binding)** 이라고 부른다.

> 함수 정의 시점이 아니라 **실행 시점에 변수 이름을 해석**하기 때문에  
> 루프 변수/외부 변수를 그대로 쓰면 “마지막 값만 보는” 현상이 발생한다.

---

### 3. 해결: 기본 인자를 이용한 값 캡처 (`lambda fr=fr: ...`)

수정된 코드:

```python
for row in df_instrument.itertuples(index=False):
    instrument_name: str = row.name
    fr = fr_dict[instrument_name]

    fr.set_download_batch_size(ICTRetrieveRunner._DOWNLOAD_BATCH_SIZE)
    fr.set_fetch_list_limit(ICTRetrieveRunner._FETCH_LIST_LIMIT)

    retrier = Retrier.retry(
        lambda fr=fr: fr.run(),
        on_retry=lambda fr=fr: fr.connect_to_instrument(),
    )
    tasks.append(asyncio.create_task(retrier))
```

여기서 핵심은 `lambda fr=fr: ...` 이다.

- 오른쪽 `fr`:
  - 루프 **현재 시점**의 `fr` 객체 (예: MI-01용 `FileRetriever`)
- 왼쪽 `fr`:
  - lambda의 **파라미터 이름 및 기본값** 역할

이 한 줄이 의미하는 것:

- “지금 이 순간의 `fr` 값을 **기본 인자로 복사해서** lambda 안에 박제하라.”
- 이후 lambda 내부에서 사용하는 `fr`는:
  - 외부 스코프의 `fr` 변수를 보는 게 아니라,
  - **자신의 기본 인자에 저장된 값**을 사용한다.

결과:

- MI-01 반복에서 생성된 lambda → `fr=MI-01용 FileRetriever`로 고정
- MI-02 반복에서 생성된 lambda → `fr=MI-02용 FileRetriever`로 고정

→ 각 태스크가 **“자기 루프에서의 fr”만 들고 가게 되어**,  
MI-01, MI-02 모두 `data_retriever.FileRetriever.run()` 이 정상적으로 호출된다.

---

### 4. 직관적 비유

- 잘못된 코드 (`lambda: fr.run()`):
  - 회의실 화이트보드에 `fr = ???` 라고 적어두고,
  - 모든 lambda가 **나중에 화이트보드에 적힌 fr를 참고**하는 방식.
  - 회의가 끝나면 화이트보드에는 **마지막 사람(MI-02)** 만 남아 있음.

- 수정 코드 (`lambda fr=fr: fr.run()`):
  - 회의 중에 각 사람의 **명함을 복사해서** 내 노트에 붙여두는 것.
  - 나중에 봐도 각 페이지에는 **각자의 명함(MI-01, MI-02)** 이 그대로 남아 있음.

---

### 5. 요약

- **문제**: 루프 안에서 `lambda: fr.run()` 형태로 클로저를 만들면,  
  파이썬의 지연 바인딩 때문에 **모든 lambda가 마지막 `fr`만 참조**하게 된다.
- **해결**: `lambda fr=fr: fr.run()` 처럼 **기본 인자**를 이용해  
  “루프 당시의 `fr`값”을 lambda 내부에 복사해 두면,  
  각 태스크가 **자기 전용 `fr`를 고정**해서 사용하게 된다.


