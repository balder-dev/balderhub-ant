from __future__ import annotations

from abc import ABC

from balderhub.ant.lib.utils.pages.base_received_antplus_page import BaseReceivedAntplusPage


class BaseHrmPage(BaseReceivedAntplusPage, ABC):
    """
    Base Heart-Rate-Monitor Page
    """
    PAGE_ID = None

    def __repr__(self):
        return (f"{self.__class__.__name__}<toggle: {int(self.toggle_bit)} "
                f"| event-time={self.heart_beat_event_time} "
                f"| beat-count={self.heart_beat_count} "
                f"| beat={self.computed_heart_rate} ({self._timestamp:.4f})>")

    def _validate_page_num(self, in_raw_data: bytes) -> None:
        """custom page num validation page -> allows toggle bit"""
        toggle_bit_adjusted_page_num = in_raw_data[0] & ~(1 << 7)
        if toggle_bit_adjusted_page_num != self.PAGE_ID:
            raise ValueError(f'raw data holds wrong page number {toggle_bit_adjusted_page_num} (toggle bit adjusted)'
                             f'(expected {self.PAGE_ID} for {self.__class__.__name__})')

    @property
    def toggle_bit(self) -> bool:
        """
        :return: the current state of the toggle bit of the current page message
        """
        unpacked_data = self._raw_unpack()
        return bool((unpacked_data[0] >> 7) & 0x01)

    @property
    def heart_beat_event_time(self) -> int:
        """
        :return: the raw heart-beat-event-time of the current page message
        """
        unpacked_data = self._raw_unpack()
        return unpacked_data[-3]

    @property
    def heart_beat_count(self) -> int:
        """
        :return: the raw heart-beat-count of the current page message
        """
        unpacked_data = self._raw_unpack()

        return unpacked_data[-2]

    @property
    def computed_heart_rate(self) -> int:
        """
        :return: the computed-heart-rate of the current page message
        """
        unpacked_data = self._raw_unpack()
        return unpacked_data[-1]
