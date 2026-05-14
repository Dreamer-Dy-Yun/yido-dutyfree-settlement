from __future__ import annotations

from decimal import Decimal

import numpy as np
import pandas as pd
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, JSON, Numeric, String as SAString, Time
from sqlalchemy.orm import DeclarativeBase


class PGDataFrameConverter:
    @staticmethod
    def convert_datetime_for_db(df: pd.DataFrame, deep_copy: bool = True) -> pd.DataFrame:
        """datetime 컬럼만 DB 입력 가능한 Python datetime/None 값으로 변환한다."""
        result = df.copy() if deep_copy else df
        for col in result.select_dtypes(include=["datetime", "datetimetz"]).columns:
            values = pd.to_datetime(result[col], errors="coerce")
            out = pd.Series(values.dt.to_pydatetime(), index=values.index, dtype="object")
            out.loc[values.isna()] = None
            result[col] = out
        return result

    @staticmethod
    def convert_numeric_for_db(
        df: pd.DataFrame,
        set_none_as: float | int | None = None,
        allow_infinity: bool = True,
        deep_copy: bool = True,
    ) -> pd.DataFrame:
        """numeric 컬럼의 NaN/inf 값을 DB 입력 정책에 맞춘다."""
        result = df.copy() if deep_copy else df
        for col in result.select_dtypes(include=["integer", "floating"]).columns:
            values = pd.to_numeric(result[col], errors="coerce")
            mask = values.notna() if allow_infinity else values.notna() & np.isfinite(values)
            result[col] = values.astype("object").where(mask, None) if set_none_as is None else values.where(mask, set_none_as)
        return result

    @staticmethod
    def convert_string_cols_by_model(df: pd.DataFrame, model: type[DeclarativeBase]) -> pd.DataFrame:
        result = df.copy()
        for col in model.__table__.columns:
            if col.name in result.columns and isinstance(col.type, SAString):
                result[col.name] = result[col.name].astype(object).where(pd.notna(result[col.name]), None)
        return result

    def convert_df_by_model(
        self,
        df: pd.DataFrame,
        model: type[DeclarativeBase],
        allow_infinity: bool = True,
        deep_copy: bool = True,
    ) -> pd.DataFrame:
        result = df.copy() if deep_copy else df
        for col in model.__table__.columns:
            if col.name not in result.columns:
                continue
            result[col.name] = self._convert_series_by_column(result[col.name], col.type, allow_infinity)
        return result

    def _convert_df_for_db(
        self,
        df: pd.DataFrame,
        table: type[DeclarativeBase],
        try_convert: bool = True,
        allow_infinity: bool = True,
    ) -> pd.DataFrame:
        if not try_convert:
            return df.copy()
        return self.convert_df_by_model(df, table, allow_infinity=allow_infinity, deep_copy=True)

    def _convert_series_by_column(self, series: pd.Series, column_type: object, allow_infinity: bool) -> pd.Series:
        if isinstance(column_type, SAString):
            return self._fix_cols_string(series)
        if isinstance(column_type, Integer):
            return self._fix_cols_integer(series)
        if isinstance(column_type, Float):
            return self._fix_cols_float(series, allow_infinity)
        if isinstance(column_type, Numeric):
            return self._fix_cols_float(series, allow_infinity).apply(self._to_decimal)
        if isinstance(column_type, DateTime):
            return self._fix_cols_datetime(series)
        if isinstance(column_type, Date):
            return self._fix_cols_date(series)
        if isinstance(column_type, Time):
            return self._fix_cols_time(series)
        if isinstance(column_type, Boolean):
            return self._fix_cols_boolean(series)
        if isinstance(column_type, JSON):
            return self._fix_cols_json(series)
        return series.astype(object).where(pd.notna(series), None)

    @staticmethod
    def _fix_cols_string(series: pd.Series) -> pd.Series:
        return series.astype(object).where(pd.notna(series), None)

    @staticmethod
    def _fix_cols_integer(series: pd.Series) -> pd.Series:
        values = pd.to_numeric(series, errors="coerce").astype("Int64")
        return values.astype(object).where(values.notna(), None)

    @staticmethod
    def _fix_cols_float(series: pd.Series, allow_infinity: bool = True) -> pd.Series:
        values = pd.to_numeric(series, errors="coerce")
        mask = values.notna() if allow_infinity else values.notna() & np.isfinite(values)
        return values.astype(object).where(mask, None)

    @staticmethod
    def _fix_cols_datetime(series: pd.Series) -> pd.Series:
        values = pd.to_datetime(series, errors="coerce")
        out = pd.Series(values.dt.to_pydatetime(), index=series.index, dtype="object")
        out.loc[values.isna()] = None
        return out

    @staticmethod
    def _fix_cols_date(series: pd.Series) -> pd.Series:
        values = pd.to_datetime(series, errors="coerce")
        out = pd.Series(values.dt.date, index=series.index, dtype="object")
        out.loc[values.isna()] = None
        return out

    @staticmethod
    def _fix_cols_time(series: pd.Series) -> pd.Series:
        values = pd.to_datetime(series, errors="coerce")
        out = pd.Series(values.dt.time, index=series.index, dtype="object")
        out.loc[values.isna()] = None
        return out

    @staticmethod
    def _fix_cols_boolean(series: pd.Series) -> pd.Series:
        def to_bool(value: object) -> bool | None:
            if pd.isna(value):
                return None
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"true", "t", "1", "y", "yes"}:
                    return True
                if normalized in {"false", "f", "0", "n", "no"}:
                    return False
            return None

        return series.astype(object).apply(to_bool)

    @staticmethod
    def _to_decimal(value: float | int | str | Decimal | None) -> Decimal | None:
        if value is None or pd.isna(value):
            return None
        return Decimal(str(value))

    @staticmethod
    def _fix_cols_json(series: pd.Series) -> pd.Series:
        return series.astype(object).where(pd.notna(series), None)


__all__ = ["PGDataFrameConverter"]
