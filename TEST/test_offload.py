# offload_demo.py
# Author: Yun Dae-Young (requested) / GPT-5 Thinking
# Purpose: Compare two offloading strategies for tasks {B-1(IO), B-2(CPU), B-3(CPU)}
# Mode A: Offload IO only, chain CPU after IO completion order
# Mode B: Offload entire B as an independent pipeline
# Python 3.10+

from __future__ import annotations
import asyncio
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from time import perf_counter
from typing import List, Tuple

# =========================
# Config (상단 선언)
# =========================
NUM_B = 4                                # B=1..NUM_B
IO_DURATIONS = [0.30, 0.10, 0.20, 0.05]  # 각 B의 B-1(IO) 시간(초) — 재현성 위해 고정값
CPU2_COST_MS = [120, 80, 150, 60]        # B-2 CPU 코스트(밀리초)
CPU3_COST_MS = [100, 140, 90, 110]       # B-3 CPU 코스트(밀리초)
CPU_WORKERS = 2                          # ProcessPoolExecutor 병렬도 (실코어 수를 크게 넘기지 말 것)
SPIN_GRANULARITY = 5000                  # busy-loop granular constant (환경에 맞춰 조정 가능)

# =========================
# 유틸
# =========================
def now_ms(start: float) -> int:
    return int((perf_counter() - start) * 1000)

def cpu_spin_ms(ms: int) -> None:
    """GIL 해소를 위해 프로세스 풀에서 돌릴 CPU-bound busy loop."""
    # 순수 파이썬 연산으로 CPU를 점유 (환경 따라 속도 다름)
    target = perf_counter() + ms / 1000.0
    x = 0
    while perf_counter() < target:
        # 약한 산술연산 반복 (연산 밀도 조절용)
        for _ in range(SPIN_GRANULARITY):
            x = (x * 1664525 + 1013904223) & 0xFFFFFFFF
    # 반환값 불필요. (최적화 방지용 누적 변수 사용)

async def io_sleep(seconds: float) -> None:
    await asyncio.sleep(seconds)

@dataclass
class StepLog:
    t_ms: int
    label: str

# =========================
# 모드 A: B-1만 오프로딩
# =========================
async def mode_a(start_t: float, executor: ProcessPoolExecutor) -> List[StepLog]:
    """
    1) 모든 B의 B-1(IO) 제출
    2) IO 완료되는 순서대로 해당 B의 B-2 → B-3 를 CPU 풀로 수행
    """
    logs: List[StepLog] = []
    loop = asyncio.get_running_loop()

    async def submit_io(b_idx: int):
        await io_sleep(IO_DURATIONS[b_idx])
        logs.append(StepLog(now_ms(start_t), f"A: {b_idx+1}-1(IO) done"))
        # 그 B의 CPU 단계 순차 실행 (동일 B 내 순서 보장)
        await loop.run_in_executor(executor, cpu_spin_ms, CPU2_COST_MS[b_idx])
        logs.append(StepLog(now_ms(start_t), f"A: {b_idx+1}-2(CPU) done"))
        await loop.run_in_executor(executor, cpu_spin_ms, CPU3_COST_MS[b_idx])
        logs.append(StepLog(now_ms(start_t), f"A: {b_idx+1}-3(CPU) done"))

    # 모든 IO 태스크 걸어두고, 완료 순으로 후속 CPU가 이어짐
    tasks = [asyncio.create_task(submit_io(i)) for i in range(NUM_B)]
    await asyncio.gather(*tasks)
    return logs

# =========================
# 모드 B: B 전체 오프로딩 (파이프라인)
# =========================
async def mode_b(start_t: float, executor: ProcessPoolExecutor) -> List[StepLog]:
    """
    각 B를 독립 파이프라인( B-1→B-2→B-3 )으로 동시 실행.
    동일 B 내부 순서는 고정, B 간 완료 순서는 비결정적.
    """
    logs: List[StepLog] = []
    loop = asyncio.get_running_loop()

    async def run_pipeline(b_idx: int):
        # B-1
        await io_sleep(IO_DURATIONS[b_idx])
        logs.append(StepLog(now_ms(start_t), f"B: {b_idx+1}-1(IO) done"))
        # B-2
        await loop.run_in_executor(executor, cpu_spin_ms, CPU2_COST_MS[b_idx])
        logs.append(StepLog(now_ms(start_t), f"B: {b_idx+1}-2(CPU) done"))
        # B-3
        await loop.run_in_executor(executor, cpu_spin_ms, CPU3_COST_MS[b_idx])
        logs.append(StepLog(now_ms(start_t), f"B: {b_idx+1}-3(CPU) done"))

    tasks = [asyncio.create_task(run_pipeline(i)) for i in range(NUM_B)]
    # 파이프라인들을 전부 제출. 완료 순서는 비결정적
    await asyncio.gather(*tasks)
    return logs

# =========================
# 실행부
# =========================
def print_section(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

async def main():
    print_section("Config")
    print(f"NUM_B={NUM_B}")
    print(f"IO_DURATIONS={IO_DURATIONS}")
    print(f"CPU2_COST_MS={CPU2_COST_MS}")
    print(f"CPU3_COST_MS={CPU3_COST_MS}")
    print(f"CPU_WORKERS={CPU_WORKERS}")

    # 공용 프로세스 풀 (CPU 단계용)
    with ProcessPoolExecutor(max_workers=CPU_WORKERS) as executor:
        # --- Mode A ---
        print_section("Mode A: offload IO only (B-1 async) -> then B-2, B-3 per IO completion")
        start_a = perf_counter()
        logs_a = await mode_a(start_a, executor)
        for lg in sorted(logs_a, key=lambda s: s.t_ms):
            print(f"[{lg.t_ms:5d} ms] {lg.label}")

        # --- Mode B ---
        print_section("Mode B: offload entire B (pipeline per B) in parallel")
        start_b = perf_counter()
        logs_b = await mode_b(start_b, executor)
        for lg in sorted(logs_b, key=lambda s: s.t_ms):
            print(f"[{lg.t_ms:5d} ms] {lg.label}")

if __name__ == "__main__":
    asyncio.run(main())
