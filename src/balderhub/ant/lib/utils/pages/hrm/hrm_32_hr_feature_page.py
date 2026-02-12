from __future__ import annotations
from ..base_antplus_page import BaseAntplusPage


class Hrm32HrFeaturePage(BaseAntplusPage):
    """page for controlling HR features"""
    PAGE_ID = 32
    _STRUCT_DATA_FORMAT = '<BBBBBBBB'
