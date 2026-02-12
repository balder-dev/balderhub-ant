from __future__ import annotations

from .base_hrm_page import BaseHrmPage


class Hrm0DefaultDataPage(BaseHrmPage):
    """
    This is the default data page without any specific information in the page specific bytes.
    """
    PAGE_ID = 0
    _STRUCT_DATA_FORMAT = '<BBBBHBB'
