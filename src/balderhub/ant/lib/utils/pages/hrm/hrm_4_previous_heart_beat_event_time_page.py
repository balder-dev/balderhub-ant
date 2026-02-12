from __future__ import annotations
from .base_hrm_page import BaseHrmPage


class Hrm4PreviousHeartBeatEventTimePage(BaseHrmPage):
    """
    This is the fourth data page in the HRM profile that can also be used as a main page. It hold some manufacturer
    specific data and the previous heart beat event time within the page-specific bytes.
    """
    PAGE_ID = 4
    _STRUCT_DATA_FORMAT = '<BBBBHBB'

    @property
    def manufacturer_specific_byte(self) -> int:
        """
        :return: returns some manufacturer specific information
        """
        return self._raw_data[1]

    @property
    def previous_heart_beat_event_time_raw(self) -> int:
        """
        :return: returns the previous heart beat event time
        """
        return int.from_bytes(self.raw_data[2:4], 'little')
