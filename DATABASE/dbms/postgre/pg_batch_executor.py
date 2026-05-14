from __future__ import annotations

from typing import Any, Awaitable, Callable, TypeAlias

import pandas as pd
from pandas import DataFrame
from sqlalchemy.ext.asyncio import AsyncSession


BatchResult: TypeAlias = dict[str, int | DataFrame | list[str]]
BatchExecutor: TypeAlias = Callable[[pd.DataFrame], Awaitable[None]]


class BatchExecutionMixin:
    async def _execute_batches(
        self,
        df: pd.DataFrame,
        session: AsyncSession,
        rows_per_batch: int,
        partial_commit: bool,
        execute_batch: BatchExecutor,
    ) -> BatchResult:
        if len(df) == 0:
            return self._batch_result(0, 0, DataFrame(), [])

        success_rows = 0
        failed_batches: list[DataFrame] = []
        errors: list[str] = []

        for batch_index, start in enumerate(range(0, len(df), rows_per_batch)):
            batch = df.iloc[start:start + rows_per_batch]
            try:
                await execute_batch(batch)
                if partial_commit:
                    await session.commit()
                success_rows += len(batch)
            except Exception as exc:
                if not partial_commit:
                    raise
                await session.rollback()
                failed_batches.append(batch)
                errors.append(self._format_batch_error(batch_index, exc))

        failed = pd.concat(failed_batches, ignore_index=False) if failed_batches else DataFrame()
        failed_rows = int(sum(len(batch) for batch in failed_batches))
        return self._batch_result(success_rows, failed_rows, failed, errors)

    @staticmethod
    def _batch_result(success_rows: int, failed_rows: int, failed: DataFrame, errors: list[str]) -> BatchResult:
        return {
            "cnt_success_rows": success_rows,
            "cnt_failed_rows": failed_rows,
            "df_failed": failed,
            "errors": errors,
        }

    @staticmethod
    def _format_batch_error(batch_index: int, exc: Exception) -> str:
        orig: Any = getattr(exc, "orig", None)
        message = str(orig) if orig else str(exc)
        return f"[batch={batch_index}] {type(exc).__name__}: {message}"
