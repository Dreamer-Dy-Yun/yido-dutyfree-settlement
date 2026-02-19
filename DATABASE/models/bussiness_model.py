###########################################
# Module name : bussiness_model.py
# Module class : 비즈니스 도메인 모델 (OCR 여권 등)
# Written by : Cursor AI / Yun Dae-young
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.01.27
# Note : OCR_PASSPORT, VERIFIED_PASSPORT, PROMPT 등
#   OCR/VERIFIED 스펙: Version 2.0.0, PROMPT 스펙: Version 0.3.0
############################################

from __future__ import annotations

from datetime import date, datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, Date, DateTime, Numeric, ForeignKey, UniqueConstraint, BigInteger, JSON
from DATABASE.models.base_model import BaseModel
from DATABASE.models.authorities_model import Tenant, User


# ---------------------------------------------------------------------------
# OCR_PASSPORT: 구매자 여권 정보 (OCR 결과값)
# 테이블 목적: 구매자의 여권 정보, 특기사항: OCR 결과값
# ---------------------------------------------------------------------------
class OcrPassport(BaseModel):
    """구매자 여권 정보 (OCR 결과). ICAO Doc 9303 Part 4 Section 4.2.2 근거."""

    __tablename__ = "ocr_passport"

    # 여권 기본 정보
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)  # 국적, 예: KOR
    passport_no: Mapped[str | None] = mapped_column(String(9), nullable=True)  # 여권번호
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 이름 (여권 표기)
    gender: Mapped[str | None] = mapped_column(String(1), nullable=True)  # M | F
    place_of_birth: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 출생지
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)  # 생년월일
    place_of_issue: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 발행지
    date_of_issue: Mapped[date | None] = mapped_column(Date, nullable=True)  # 발행일
    date_of_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)  # 만료일
    authority: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 발급기관
    coordinate: Mapped[dict[str, int] | None] = mapped_column(JSON, nullable=True)  # 이미지 내 좌표
    
    # 해싱된 이미지 (SHA-256, 64자)
    hash_img: Mapped[str] = mapped_column(String(64), nullable=False)

    # 테넌트 (이미지 등록 소유 회사)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 관계 (Tenant 쪽 back_populates는 필요 시 authorities_model에 추가)
    tenant: Mapped["Tenant"] = relationship("Tenant", foreign_keys=[tenant_id], lazy="selectin")



# ---------------------------------------------------------------------------
# OCR_RECEIPT: 구매자 영수증 정보 (OCR 결과값)
# 테이블 목적: 영수증 OCR 결과, 특기사항: OCR 결과값
# ---------------------------------------------------------------------------
class OcrReceipt(BaseModel):
    """구매자 영수증 정보 (OCR 결과). 영수증 상 데이터 OCR 인식값."""

    __tablename__ = "ocr_receipt"

    dutyfree_company: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 면세점 구분, 예: LOTTE
    group_no: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 그룹 번호
    receipt_no: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 영수증 번호(교환권)
    passport_no: Mapped[str | None] = mapped_column(String(9), nullable=True)  # 구매자 여권 번호
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 구매자 이름
    coordinate: Mapped[dict[str, int] | None] = mapped_column(JSON, nullable=True)  # 이미지 내 좌표

    # 해싱된 이미지 (SHA-256, 64자)
    hash_img: Mapped[str] = mapped_column(String(64), nullable=False)

    # 테넌트 (이미지 등록 소유 회사)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 관계
    tenant: Mapped["Tenant"] = relationship("Tenant", foreign_keys=[tenant_id], lazy="selectin")

    __table_args__ = (
        UniqueConstraint("hash_img", "tenant_id", name="uq_ocr_receipt_hash_tenant"),
    )


# ---------------------------------------------------------------------------
# VERIFIED_RECEIPT: 검증된 구매자 영수증 정보
# OCR_RECEIPT와 초기 레코드 구조 유사. 복합 유니크(dutyfree_company, receipt_no, tenant_id)
# 수정 시: 새 유니크로 업서트(is_verified=True), 기존 레코드는 is_verified=False 후 삭제
# ---------------------------------------------------------------------------
class VerifiedReceipt(BaseModel):
    """검증된 구매자 영수증 정보. 인간 작업자 확인/정정 플래그 포함."""

    __tablename__ = "verified_receipt"

    # 복합 유니크 키 구성 컬럼 (NOT NULL)
    dutyfree_company: Mapped[str] = mapped_column(String(30), nullable=False)  # 면세점 구분, 예: LOTTE
    receipt_no: Mapped[str] = mapped_column(String(30), nullable=False)  # 영수증 번호(교환권)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 영수증 기본 정보 (nullable, 작업자 수정·확정 값)
    group_no: Mapped[str | None] = mapped_column(String(30), nullable=True)
    passport_no: Mapped[str | None] = mapped_column(String(9), nullable=True)  # 예: M1234****
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 예: Y***********G

    # 확인(변경)자 [MainDB] User
    verifier_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    verifier_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 해싱된 이미지 (SHA-256, 64자), 확인/정정 플래그
    hash_img: Mapped[str] = mapped_column(String(64), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 인간 작업자 확인 여부
    is_corrected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 확인자에 의한 변경 여부 (통계용)

    # 관계
    tenant: Mapped["Tenant"] = relationship("Tenant", foreign_keys=[tenant_id], lazy="selectin")
    verifier: Mapped["User | None"] = relationship("User", foreign_keys=[verifier_id], lazy="selectin")

    __table_args__ = (
        UniqueConstraint("dutyfree_company", "receipt_no", "tenant_id", name="uq_verified_receipt_duty_receipt_tenant"),
    )


# ---------------------------------------------------------------------------
# VERIFIED_PASSPORT: 검증된 구매자 여권 정보
# OCR_PASSPORT와 초기 레코드 구조 유사. 복합 유니크(nationality, passport_no, tenant_id)
# 수정 시: 새 유니크로 업서트(is_verified=True), 기존 레코드는 is_verified=False 후 삭제
# ---------------------------------------------------------------------------
class VerifiedPassport(BaseModel):
    """검증된 구매자 여권 정보. 인간 작업자 확인/정정 플래그 포함."""

    __tablename__ = "verified_passport"

    # 복합 유니크 키 구성 컬럼 (NOT NULL)
    nationality: Mapped[str] = mapped_column(String(3), nullable=False)  # 국적, 예: KOR
    passport_no: Mapped[str] = mapped_column(String(9), nullable=False)  # 여권번호
    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 여권 기본 정보 (nullable)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(1), nullable=True)  # M | F
    place_of_birth: Mapped[str | None] = mapped_column(String(50), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    place_of_issue: Mapped[str | None] = mapped_column(String(50), nullable=True)
    date_of_issue: Mapped[date | None] = mapped_column(Date, nullable=True)
    authority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    date_of_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)

    # 확인(변경)자 [MainDB] User
    verifier_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    verifier_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 해싱된 여권 이미지 (SHA-256, 64자), 확인/정정 플래그
    hash_img: Mapped[str] = mapped_column(String(64), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 인간 작업자 확인 여부
    is_corrected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 확인자에 의한 변경 여부 (통계용)

    # 관계
    tenant: Mapped["Tenant"] = relationship("Tenant", foreign_keys=[tenant_id], lazy="selectin")
    verifier: Mapped["User | None"] = relationship("User", foreign_keys=[verifier_id], lazy="selectin")

    __table_args__ = (
        UniqueConstraint("nationality", "passport_no", "tenant_id", name="uq_verified_passport_nat_pass_tenant"),
    )


# ---------------------------------------------------------------------------
# PROMPT: 사용 프롬프트 이력 (MainDB, 모델 관리)
# 프롬프트를 SHA-256 해시한 값으로 유니크 관리
# ---------------------------------------------------------------------------
class Prompt(BaseModel):
    """사용 프롬프트 이력. 프롬프트 해시로 유니크 관리."""

    __tablename__ = "prompt"

    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)  # SHA-256 해시
    prompt: Mapped[str] = mapped_column(Text, nullable=False)  # 프롬프트 텍스트
    note: Mapped[str | None] = mapped_column(Text, nullable=True)  # 노트 (자동 입력 아님)



# ---------------------------------------------------------------------------
# IMAGE: 이미지 파일 관리 (MainDB)
# 여권/영수증/복수 영수증 등 종류 구분 없이 동일 테이블로 관리
# ---------------------------------------------------------------------------
class Image(BaseModel):
    """이미지 파일 관리. SHA-256 해시로 동일성 확인, 회사별 유니크."""

    __tablename__ = "image"

    hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA-256, 이미지 동일성 확인용
    path: Mapped[str] = mapped_column(Text, nullable=False)  # 이미지 경로
    exists: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 파일 존재 여부
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True
    )  # 이미지 등록(소유) 회사

    # 관계
    tenant: Mapped["Tenant"] = relationship("Tenant", foreign_keys=[company_id], lazy="selectin")

    __table_args__ = (
        UniqueConstraint("hash", "company_id", name="uq_image_hash_company"),
    )




# ---------------------------------------------------------------------------
# MATCHED: EDI 정보 - 여권-영수증 매칭 및 이후 매칭
# 여권 정보는 JOIN으로 조회. receipt_no 스펙상 VERIFIED_RECEIPT.receipt_no 참조(논리적 연결)
# ---------------------------------------------------------------------------
class Matched(BaseModel):
    """매칭된 EDI 정보. 여권-영수증 매칭 및 이후 매칭."""

    __tablename__ = "matched"

    passport_no: Mapped[str | None] = mapped_column(String(9), nullable=True)  # 여권번호
    dutyfree_operator: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 면세점명 (신라/롯데)
    dutyfree_branch: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 면세지점명
    datetime_original: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 원 판매일시
    datetime_purchase: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 구입일시
    group_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 그룹 번호
    receipt_no: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)  # 영수증 번호(교환권)
    product_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 상품코드
    original_receipt_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 원영수증 번호
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 카테고리
    brand: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 브랜드명
    sku: Mapped[str | None] = mapped_column(String(50), nullable=True)  # SKU
    product_name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 제품명 (53자 확인됨)
    ref_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 참조번호
    quantity: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 판매 수량
    gross_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액($)
    net_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액($)
    discount_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총할인액($)
    gross_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액(원)
    net_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액(원)
    discount_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총할인액(원)
    used_point: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 사용된 포인트(추정)
    point: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 포인트
    rebate_amount: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 리베이트 금액
    is_matched: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # 매칭여부



# ---------------------------------------------------------------------------
# EDI_SILLA: EDI 정보 (MainDB, 신라)
# 백업 및 검증용. 스펙에 FK 없음 (VERIFIED_RECEIPT 참조 없음)
# ---------------------------------------------------------------------------
class EdiSilla(BaseModel):
    """EDI 정보 (신라). 백업 및 검증용."""

    __tablename__ = "edi_silla"

    branch: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 점, 예: 서울점
    original_sales_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 원매출일자 (없을 수 있음)
    sales_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 매출일자
    travel_agency_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 여행사명
    travel_agency_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 여행사코드
    group_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 그룹번호
    lead_guide_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 대표가이드
    birth_year: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 고객 출생연도 (85****)
    customer_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 고객명
    bill_no: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # BILL 번호
    bill_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # BILL 상태
    product_location: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 상품위치
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 카테고리
    brand_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 브랜드명
    product_name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 상품명
    product_code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # 상품코드
    ref_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # REF NO
    aging_days: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # Aging
    sales_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 판매형태
    sales_quantity: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 판매수량
    unit_price_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 판매가($)
    gross_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액($)
    gross_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액(￦)
    net_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액($)
    net_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액(￦)
    discount_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 할인액($)
    discount_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 할인액(￦)



# ---------------------------------------------------------------------------
# EDI_LOTTE: EDI 정보 (MainDB, 롯데)
# 백업 및 검증용, 2026.10.09 조회 기준. SILLA_EDI와 컬럼 상이
# ---------------------------------------------------------------------------
class EdiLotte(BaseModel):
    """EDI 정보 (롯데). 교환권번호·상품코드 등."""

    __tablename__ = "edi_lotte"

    branch: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 점구분, 예: 명동본점
    original_sales_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 원매출일자 (없을 수 있음)
    sales_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 매출일자
    travel_agency_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 여행사
    travel_agency_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 여행사코드
    guide_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 가이드
    guide_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 가이드코드
    sales_origin_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 수입/로컬
    group_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 단체번호
    vip_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # VIP번호
    voucher_no: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # 교환권번호
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 카테고리
    brand_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 브랜드
    product_name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 상품명
    product_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 상품구분 (SKU)
    product_code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # 상품코드
    ref_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Ref.No
    gross_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액($)
    net_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액($)
    gross_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액(원)
    net_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액(원)
    discount_rate: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 할인율(%)


# ---------------------------------------------------------------------------
# LLM_USAGE: LLM 사용정보 로그 (MainDB)
# ---------------------------------------------------------------------------
class LlmUsage(BaseModel):
    """LLM 사용정보 로그."""

    __tablename__ = "llm_usage"

    llm_model: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 사용된 LLM명
    hash_prompt: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # 사용된 프롬프트 hash
    ocr_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 사용된 OCR 명
    hash_img: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # 해싱된 이미지 (SHA-256)
    token_input: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 입력토큰 사용량
    token_output: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 출력토큰 사용량
    token_total: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총 토큰 사용량
    tenant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True
    )  # 이미지 등록(소유) 회사

    # 관계
    tenant: Mapped["Tenant"] = relationship("Tenant", foreign_keys=[tenant_id], lazy="selectin")

