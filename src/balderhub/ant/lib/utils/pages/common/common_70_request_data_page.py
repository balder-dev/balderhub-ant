from __future__ import annotations

import struct
from ..base_antplus_page import BaseAntplusPage


class Common70RequestDataPage(BaseAntplusPage):
    """
    Common data page 70 to request a specific data page from the other device
    """
    PAGE_ID = 70

    _STRUCT_DATA_FORMAT = '<BBBBBBBB'

    @classmethod
    def create(
            cls,
            requested_transmission_response: int,  # TODO use bit field?
            requested_page_no: int,
            command_type: int,
    ) -> Common70RequestDataPage:
        """
        Creates a new message type with the provided field values.

        :param requested_transmission_response: the requested transmission response byte
        :param requested_page_no: the page number to request
        :param command_type: the command type to send
        :return: the ready to send message
        """
        reserved = 0xFF

        data = struct.pack(
            cls._STRUCT_DATA_FORMAT,
            cls.PAGE_ID,
            reserved,
            reserved,
            reserved,
            reserved,
            requested_transmission_response,
            requested_page_no,
            command_type,
        )
        return cls(data)

    @property
    def descriptor_byte1(self):
        """
        :return: returns the descriptor byte 1
        """
        return self._raw_data[3]

    @property
    def descriptor_byte2(self):
        """
        :return: returns the descriptor byte 2
        """
        return self._raw_data[4]

    @property
    def requested_transmission_response(self) -> int:
        """
        :return: returns the requested transmission response
        """
        return self._raw_data[5]

    @property
    def requested_no_of_times(self) -> int:
        """
        :return: returns the number of times, the device should respond with the requested page
        """
        return self.requested_transmission_response & ~(1 << 7)

    @property
    def requested_ack_response(self) -> bool:
        """
        :return: returns True if the page object asks for a response as ACK message instead of BROADCAST message
        """
        return bool(self.requested_transmission_response & (1 << 7))

    @property
    def requested_page_no(self) -> int:
        """
        :return: returns the requested page number
        """
        return self._raw_data[6]

    @property
    def command_type(self) -> int:
        """
        :return: returns the requested command type
        """
        return self._raw_data[7]
