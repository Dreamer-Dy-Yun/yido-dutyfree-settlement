###########################################
# Module name : service_tenant_deletion.py
# Module class : TenantDeletionService
# Written by : Yun Dae-young
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.03.20
############################################

import asyncio
import os
import shutil
from pathlib import Path
from typing import Any

from CUSTOMIZED.cust_logger import logger
from DATABASE.models.public_model import Tenant as PublicTenant


class TenantDeletionService:
    """
    테넌트 삭제 시 물리 파일까지 함께 제거한다.

    "해당 테넌트 안의 데이터는 다 지워야 한다" 요구에 맞춰,
    tenant.dir_base 아래 tenant_root 전체를 삭제한다.
    """

    @staticmethod
    async def delete_tenant_files(
        tenant: PublicTenant,
        *,
        retries: int = 3,
    ) -> dict[str, Any]:
        root_dir = os.getenv("ROOT_DIR", "D:\\")
        base_root = Path(root_dir).resolve()

        dir_base = str(getattr(tenant, "dir_base", "") or "").strip()
        if not dir_base:
            raise ValueError("tenant.dir_base 가 비어있습니다. 파일 삭제를 진행할 수 없습니다.")

        tenant_root = Path(dir_base)
        if not tenant_root.is_absolute():
            tenant_root = base_root / tenant_root
        tenant_root = tenant_root.resolve()

        # 안전장치: 삭제 대상이 base_root 밖이면 중단
        try:
            tenant_root.relative_to(base_root)
        except ValueError as e:
            raise RuntimeError(
                f"테넌트 삭제 대상 경로가 ROOT_DIR 밖입니다. base_root={base_root}, tenant_root={tenant_root}"
            ) from e

        existed = tenant_root.exists()
        if not existed:
            return {
                "deleted": False,
                "existed": False,
                "base_root": str(base_root),
                "tenant_root": str(tenant_root),
            }

        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                await asyncio.to_thread(shutil.rmtree, tenant_root)
                last_error = None
                break
            except Exception as e:
                last_error = e
                logger.warning(
                    f"테넌트 폴더 삭제 실패. attempt={attempt + 1}/{retries}, tenant_root={tenant_root}, error={e}"
                )
                # Windows에서 파일 lock이 걸린 경우를 대비해 재시도
                await asyncio.sleep(1.0 * (attempt + 1))

        if last_error is not None and tenant_root.exists():
            raise RuntimeError(f"테넌트 폴더 삭제에 실패했습니다: tenant_root={tenant_root}, error={last_error}")

        return {
            "deleted": True,
            "existed": True,
            "base_root": str(base_root),
            "tenant_root": str(tenant_root),
        }

