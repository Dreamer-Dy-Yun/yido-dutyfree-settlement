from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select

from DATABASE import models
from DATABASE.dbms import DBManager


def build_archive_db_updated_by(current_user: models.User) -> str:
    """
    archive_* 테이블의 db_updated_by에 넣을 감사 문자열.

    - id가 아니라 name/alias/e_mail 문자열을 저장
    - snapshot 성격이므로 문자열로 고정 기록
    - BaseModel(db_updated_by)는 String(100) 제한이 있어 길면 잘라 저장
    """

    name = (getattr(current_user, "name", None) or "").strip()
    alias = (getattr(current_user, "alias", None) or "").strip()
    e_mail = (getattr(current_user, "e_mail", None) or "").strip()
    s = f"name : {name}, alias : {alias}, e_mail : {e_mail}"
    return s[:100]


async def archive_verified_row_by_uuid(
    db: DBManager,
    schemas: list[str],
    verified_model: type,
    archive_model: type,
    uuid_record: str,
    current_user: models.User,
) -> None:
    """
    verified_* 1개 레코드를 읽어서 archive_* 1개로 스냅샷 insert.

    정책:
    - archive_model의 컬럼이 기준이며, verified_model 컬럼을 복사하되 id는 제외한다.
    - db_updated_by만 build_archive_db_updated_by(current_user) 값으로 덮어쓴다.
    """

    uuid_record = (uuid_record or "").strip()
    if not uuid_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="uuid_record가 비어 있습니다.")

    actor_updated_by = build_archive_db_updated_by(current_user)

    async with db.open_session(schemas=schemas) as session:
        stmt = select(verified_model).where(verified_model.uuid_record == uuid_record)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"verified 레코드를 찾을 수 없습니다. uuid_record={uuid_record}",
            )

        verified_cols = verified_model.__table__.columns
        archive_cols = archive_model.__table__.columns

        data: dict[str, Any] = {}
        for col in verified_cols:
            col_name = col.name
            if col_name == "id":
                continue
            if col_name not in archive_cols:
                continue
            data[col_name] = getattr(row, col_name)

        if "db_updated_by" in archive_cols:
            data["db_updated_by"] = actor_updated_by

        await session.execute(archive_model.__table__.insert().values(**data))

