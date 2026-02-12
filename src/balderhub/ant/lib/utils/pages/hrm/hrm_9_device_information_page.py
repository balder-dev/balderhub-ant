from __future__ import annotations
from .base_hrm_page import BaseHrmPage
from ...page_message_collection import PageMessageCollection


class Hrm9DeviceInformationPage(BaseHrmPage):
    """
    This is the ninth data page in the HRM profile that holds some device information within the page-specific
    bytes.
    """
    PAGE_ID = 9
    _STRUCT_DATA_FORMAT = '<BBBBHBB'

    @property
    def heart_beat_event_type(self) -> int:
        """
        :return: returns the heart beat event type (0: measured; 1: computed)
        """
        return self._raw_data[1] & ((1 << 1) | (1 << 0))

    @classmethod
    def validate_messages(
            cls,
            of_msg_collection: PageMessageCollection
    ) -> None:
        """
        Method to validate the correctness of messages from this type

        :param of_msg_collection: the message collection that should be validated (will automatically be filtered for
                                  messages from :class:`Hrm9DeviceInformationPage`)
        """
        msgs_of_interest = of_msg_collection.filter_by_type(page_type=cls)

        for msg in msgs_of_interest:
            assert (msg.raw_data[1] & 0xFC) == 0xFC, \
                (f"reserved bits in data byte 1 are not 0xFC (full byte is {hex(msg.raw_data[1])}) "
                 f"for message {msg}")
            assert msg.raw_data[2] == 0xFF, \
                f"reserved byte 2 is not 0xFF, is {hex(msg.raw_data[2])} for message {msg}"
            assert msg.raw_data[3] == 0xFF, \
                f"reserved byte 2 is not 0xFF, is {hex(msg.raw_data[3])} for message {msg}"
