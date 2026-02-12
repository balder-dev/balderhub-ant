from __future__ import annotations
from .base_hrm_page import BaseHrmPage


class Hrm5SwimIntervalSummaryPage(BaseHrmPage):
    """
    This is the fifth data page in the HRM profile that holds information about swiming intervals within the
    page-specific bytes.
    """
    PAGE_ID = 5
    _STRUCT_DATA_FORMAT = '<BBBBHBB'

    @property
    def interval_average_heart_rate(self):
        """
        :return: returns the average heart rate within the interval
        """
        return self.raw_data[1]

    @property
    def interval_maximum_heart_rate(self):
        """
        :return: returns the maximum heart rate within the interval
        """
        return self.raw_data[2]

    @property
    def session_average_heart_rate(self):
        """
        :return: returns the average heart rate within the session
        """
        return self.raw_data[3]
