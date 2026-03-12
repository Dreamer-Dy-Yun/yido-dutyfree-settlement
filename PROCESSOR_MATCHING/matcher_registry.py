from typing import Type

from PROCESSOR_MATCHING.matcher import PassportReceiptMatcher
from PROCESSOR_MATCHING.matchers.matcher_silla import PRM_Silla
from PROCESSOR_MATCHING.matchers.matcher_lotte import PRM_Lotte


dict_matcher: dict[str, Type[PassportReceiptMatcher]] = {
    "silla": PRM_Silla,
    "lotte": PRM_Lotte,
}

