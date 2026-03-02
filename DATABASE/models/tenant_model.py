###########################################
# Module name : tenant_model.py
# Module class : Tenant 스키마 모델 (OCR 여권 등)
# Written by : Cursor AI / Yun Dae-young
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2026.02.20
# Note : Tenant 스키마에 저장되는 모델들
#   OCR_PASSPORT, VERIFIED_PASSPORT, PROMPT 등
#   OCR/VERIFIED 스펙: Version 2.0.0, PROMPT 스펙: Version 0.3.0
############################################

from __future__ import annotations

from datetime import date, datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, Date, DateTime, Numeric, ForeignKey, UniqueConstraint, BigInteger, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from DATABASE.models.base_model import BaseModel
from enum import Enum

class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"

# ---------------------------------------------------------------------------
# USER: 사용자 정보 관리 (Tenant 스키마)
# 테이블 목적: 사용자 정보 관리, 현재는 테넌트 하나당 유저 하나 예정
# Version: 2.0.0, 작성자: 윤대영
# ---------------------------------------------------------------------------
class User(BaseModel):
    """사용자 정보 관리 (Tenant 스키마)"""
    __tablename__ = "user"
    
    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 유저명
    alias: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 별칭 (랜덤 생성)
    e_mail: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)  # 이메일 (Unique)
    password: Mapped[str] = mapped_column(String(64), nullable=False)  # 해싱값(SHA-256)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.USER.value, nullable=False)  # UserRole enum value를 문자열로 저장
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)  # 소속 부서
    contact: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)  # 연락처 (Unique, 국가번호 포함)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)  # 계정 활성화 여부
    
    def __repr__(self) -> str:
        return f"<User(name={self.name}, e_mail={self.e_mail}, is_active={self.is_active})>"


# ---------------------------------------------------------------------------
# OCR_PASSPORT: 구매자 여권 정보 (OCR 결과값)
# 테이블 목적: 구매자의 여권 정보, 특기사항: OCR 결과값
# Version: 2.0.0, 작성자: 윤대영
# ---------------------------------------------------------------------------
class OcrPassport(BaseModel):
    """구매자 여권 정보 (OCR 결과). ICAO Doc 9303 Part 4 Section 4.2.2 근거."""
    __tablename__ = "ocr_passport"

    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)  # 국가코드
    passport_no: Mapped[str | None] = mapped_column(String(9), nullable=True)  # 여권번호
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 이름
    gender: Mapped[str | None] = mapped_column(String(1), nullable=True)  # 성별 [M|F]
    place_of_birth: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 출생지
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)  # 생년월일
    place_of_issue: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 발행지
    date_of_issue: Mapped[date | None] = mapped_column(Date, nullable=True)  # 발행일
    authority: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 발급기관
    date_of_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)  # 만료일
    coordinate: Mapped[dict[str, int] | None] = mapped_column(JSONB, nullable=False, index=True)  # 이미지 좌표 (COMPOSITE)
    hash_img: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # 해싱된 이미지 (SHA-256, COMPOSITE)

    __table_args__ = (
        UniqueConstraint("hash_img", "coordinate", name="uq_ocr_passport_hash_coordinate"),
    )



# ---------------------------------------------------------------------------
# OCR_RECEIPT: 구매자의 영수증 정보 (OCR 결과값)
# 테이블 목적: 영수증 OCR 결과, 특기사항: OCR 결과값
# Version: 2.0.0, 작성자: 윤대영
# ---------------------------------------------------------------------------
class OcrReceipt(BaseModel):
    """구매자 영수증 정보 (OCR 결과). 영수증 상 데이터 OCR 인식값."""
    __tablename__ = "ocr_receipt"

    dutyfree_company: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 면세점 구분
    group_no: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 그룹 번호
    receipt_no: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 영수증 번호(교환권)
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)  # 국가코드
    passport_no: Mapped[str | None] = mapped_column(String(9), nullable=True)  # 구매자 여권 번호
    purchaser: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 구매자 이름
    coordinate: Mapped[dict[str, int] | None] = mapped_column(JSONB, nullable=False, index=True)  # 이미지 좌표 (COMPOSITE)
    hash_img: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # 해싱된 이미지 (COMPOSITE)

    __table_args__ = (
        UniqueConstraint("hash_img", "coordinate", name="uq_ocr_receipt_hash_coordinate"),
    )


# ---------------------------------------------------------------------------
# VERIFIED_RECEIPT: 구매자의 영수증 정보
# Version: 2.0.0, 작성자: 윤대영
# ※ 원본 사진이 없더라도 삭제하지 않음
# ※ 초기 레코드는 OCR_RECEIPT와 거의 같도록 기술
# ※ 레코드 수정 입력시, 유니크키(복합)가 수정될 경우, 수정된 유니크키(복합)내용으로 업서트 (is_verified = True)
# ※ 수정전의 유니크키(복합)을 가지며, is_verified = False 인 레코드를 삭제 (오기입 레코드 삭제)
# ※ 가능하다면 업데이트 마다 OCR_RECEIPT를 비교
# ---------------------------------------------------------------------------
class VerifiedReceipt(BaseModel):
    """검증된 구매자 영수증 정보. 인간 작업자 확인/정정 플래그 포함."""
    __tablename__ = "verified_receipt"

    dutyfree_company: Mapped[str] = mapped_column(String(30), nullable=False)  # 면세점 구분 (COMPOSITE)
    group_no: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 그룹 번호
    receipt_no: Mapped[str] = mapped_column(String(30), nullable=False)  # 영수증 번호(교환권) (COMPOSITE)
    passport_no: Mapped[str | None] = mapped_column(String(9), nullable=True)  # 구매자 여권 번호
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 구매자 이름
    verifier_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)  # 확인(변경)자 식별번호
    verifier_name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 확인(변경)자 사용자명
    hash_img: Mapped[str] = mapped_column(String(64), nullable=False)  # 해싱된 영수증 이미지
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 확인 여부
    is_corrected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 확인자에 의한 변경 유부

    verifier: Mapped["User | None"] = relationship("User", foreign_keys=[verifier_id], lazy="selectin")

    __table_args__ = (
        UniqueConstraint("dutyfree_company", "receipt_no", name="uq_verified_receipt_duty_receipt"),
    )


# ---------------------------------------------------------------------------
# VERIFIED_PASSPORT: 검증된 구매자 여권 정보
# 테이블 목적: 구매자의 여권 정보
# Version: 2.0.0, 작성자: 윤대영
# ---------------------------------------------------------------------------
class VerifiedPassport(BaseModel):
    """검증된 구매자 여권 정보. 인간 작업자 확인/정정 플래그 포함."""
    __tablename__ = "verified_passport"

    country_code: Mapped[str] = mapped_column(String(3), nullable=False)  # 국적 (COMPOSITE)
    passport_no: Mapped[str] = mapped_column(String(9), nullable=False)  # 여권번호 (COMPOSITE)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 이름
    gender: Mapped[str | None] = mapped_column(String(1), nullable=True)  # 성별 [M|F]
    place_of_birth: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 출생지
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)  # 생년월일
    place_of_issue: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 발행지
    date_of_issue: Mapped[date | None] = mapped_column(Date, nullable=True)  # 발행일
    authority: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 발급기관
    date_of_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)  # 만료일
    verifier_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)  # 확인(변경)자 식별번호
    verifier_name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 확인(변경)자 사용자명
    hash_img: Mapped[str] = mapped_column(String(64), nullable=False)  # 해싱된 여권 이미지 (SHA-256)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 확인 여부
    is_corrected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 확인자에 의한 변경 유무

    verifier: Mapped["User | None"] = relationship("User", foreign_keys=[verifier_id], lazy="selectin")

    __table_args__ = (
        UniqueConstraint("country_code", "passport_no", name="uq_verified_passport_country_pass"),
    )


# ---------------------------------------------------------------------------
# PROMPT: 사용 프롬프트 이력
# 테이블 목적: 모델 관리, 사용 프롬프트 이력 관리
# Version: 0.3.0, 작성자: 윤대영
# ---------------------------------------------------------------------------
class Prompt(BaseModel):
    """사용 프롬프트 이력. 프롬프트 해시로 유니크 관리."""
    __tablename__ = "prompt"

    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)  # 프롬프트 해시 (SHA-256)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, index=True)  # 프롬프트
    note: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)  # 노트



# ---------------------------------------------------------------------------
# IMAGE: 이미지 파일 관리
# 테이블 목적: 이미지 파일 관리
# Version: 0.3.0, 작성자: 윤대영
# ---------------------------------------------------------------------------
class Image(BaseModel):
    """이미지 파일 관리. SHA-256 해시로 동일성 확인, 회사별 유니크."""
    __tablename__ = "image"

    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)  # 이미지 해싱값 (SHA-256)
    path: Mapped[str] = mapped_column(Text, nullable=False, index=True)  # 경로
    exists: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)  # 파일 존재 여부




# ---------------------------------------------------------------------------
# MATCHED: EDI 정보 (여권-영수증 매칭과 그 이후의 매칭으로 테이블 분리 고려중)
# 테이블 목적: EDI 정보(여권-영수증 매칭과 그 이후의 매칭으로 테이블 분리 고려중)
# Version: 2.0.0, 작성자: 윤대영
# ※ 여권 정보는 JOIN으로 받을 것
# ※ receipt_no는 VERIFIED_RECEIPT.receipt_no 참조 (논리적 연결, 복합 유니크 키이므로 FK 제약 없음)
# ---------------------------------------------------------------------------
class Matched(BaseModel):
    """매칭된 EDI 정보. 여권-영수증 매칭 및 이후 매칭."""
    __tablename__ = "matched"

    passport_no: Mapped[str | None] = mapped_column(String(9), nullable=True)  # 여권번호
    dutyfree_operator: Mapped[str] = mapped_column(String(30), nullable=False)  # 면세점명 (COMPOSITE)
    dutyfree_branch: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 면세지점명
    datetime_original: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 원 판매일시
    datetime_purchase: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 구입일시
    group_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 그룹 번호
    receipt_no: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # 영수증 번호(교환권) (COMPOSITE, VERIFIED_RECEIPT.receipt_no 참조)
    product_code: Mapped[str] = mapped_column(String(50), nullable=False)  # 상품코드 (COMPOSITE)
    original_receipt_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 원영수증 번호
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 카테고리
    brand: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 브랜드명
    sku: Mapped[str | None] = mapped_column(String(50), nullable=True)  # SKU
    product_name: Mapped[str | None] = mapped_column(String, nullable=True)  # 제품명
    ref_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 참조번호
    quantity: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 판매 수량
    gross_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액($)
    net_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액($)
    discount_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총할인액($)
    gross_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액(원)
    net_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액(원)
    discount_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총할인액(원)
    used_point: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 사용된 포인트
    point: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 포인트
    rebate_amount: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 리베이트 금액
    is_matched: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # 매칭여부

    __table_args__ = (
        UniqueConstraint("dutyfree_operator", "receipt_no", "product_code", name="uq_matched_operator_receipt_product"),
    )




# ---------------------------------------------------------------------------
# EDI_SILLA: EDI 정보
# 테이블 목적: EDI 정보
# Version: 2.0.0, 작성자: 윤대영
# ※ 백업 및 검증용도
# ---------------------------------------------------------------------------
class EdiSilla(BaseModel):
    """EDI 정보 (신라). 백업 및 검증용도."""
    __tablename__ = "edi_silla"

    branch: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 점
    original_sales_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 원매출일자
    sales_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 매출일자
    travel_agency_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 여행사명
    travel_agency_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 여행사코드
    group_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 그룹번호
    lead_guide_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 대표가이드
    birth_year: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 출생연도
    customer_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 고객명
    bill_no: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # BILL 번호 (COMPOSITE)
    bill_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # BILL 상태
    product_location: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 상품위치
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 카테고리
    brand_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 브랜드명
    product_name: Mapped[str | None] = mapped_column(String, nullable=True)  # 상품명
    product_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 상품코드 (COMPOSITE)
    ref_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # REF NO
    aging: Mapped[float] = mapped_column(Numeric(precision=19, scale=4), nullable=False)  # Aging
    sales_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 판매형태
    sales_quantity: Mapped[float] = mapped_column(Numeric(precision=19, scale=4), nullable=False)  # 판매수량
    unit_price_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 판매가($)
    gross_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액($)
    gross_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액(원)
    net_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액($)
    net_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액(원)
    discount_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 할인액($)
    discount_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 할인액(원)

    __table_args__ = (
        UniqueConstraint("bill_no", "product_code", "sales_quantity", "aging", name="uq_edi_silla_bill_product_quantity_aging"),
    )




# ---------------------------------------------------------------------------
# EDI_LOTTE: EDI 정보
# 테이블 목적: EDI 정보
# Version: 2.0.0, 작성자: 윤대영
# ※ 백업 및 검증용도
# ※ 2026.10.09 조회 기준 테이블
# ※ 이전에 파악된 내용과 컬럼 상이
# ---------------------------------------------------------------------------
class EdiLotte(BaseModel):
    """EDI 정보 (롯데). 백업 및 검증용도."""
    __tablename__ = "edi_lotte"

    branch: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 점구분
    original_sales_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 원매출일자
    sales_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 매출일자
    travel_agency_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 여행사
    travel_agency_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 여행사코드
    guide_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 가이드
    guide_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 가이드코드
    sales_origin_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 수입/로컬
    group_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 단체번호
    vip_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # VIP번호
    voucher_no: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 교환권번호 (COMPOSITE)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 카테고리
    brand_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 브랜드
    product_name: Mapped[str | None] = mapped_column(String, nullable=True)  # 상품명
    product_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 상품구분
    product_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 상품코드 (COMPOSITE)
    ref_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Ref.No
    gross_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액($)
    net_sales_amount_usd: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액($)
    gross_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총매출액(원)
    net_sales_amount_krw: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 순매출액(원)
    discount_rate: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 할인율

    __table_args__ = (
        UniqueConstraint("voucher_no", "product_code", name="uq_edi_lotte_voucher_product"),
    )


# ---------------------------------------------------------------------------
# LLM_USAGE: LLM 사용정보 로그
# 테이블 목적: EDI 정보
# Version: 2.0.0, 작성자: 윤대영
# ※ LLM 사용정보 로그
# ---------------------------------------------------------------------------
class LlmUsage(BaseModel):
    """LLM 사용정보 로그."""
    __tablename__ = "llm_usage"

    llm_model: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 사용된 LLM명
    hash_prompt: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # 사용된 프롬프트 hash (COMPOSITE)
    ocr_name: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 사용된 OCR 명
    hash_img: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # 해싱된 이미지 (COMPOSITE)
    token_input: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 입력토큰 사용량
    token_output: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 출력토큰 사용량
    token_total: Mapped[float | None] = mapped_column(Numeric(precision=19, scale=4), nullable=True)  # 총 토큰 사용량

    __table_args__ = (
        UniqueConstraint("hash_prompt", "hash_img", name="uq_llm_usage_prompt_img"),
    )
