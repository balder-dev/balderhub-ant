from __future__ import annotations
import struct

from ..base_antplus_page import BaseAntplusPage


class Common76ModeSettingsPage(BaseAntplusPage):
    """
    This page allows to change the mode settings of the device.
    """
    PAGE_ID = 76
    _STRUCT_DATA_FORMAT = '<BBBBBBBB'

    @classmethod
    def create(
            cls,
            sport_node: int,
            sub_sport_mode: int,
    ) -> Common76ModeSettingsPage:
        """
        Creates a new message type with the provided field values.

        :param sport_node: the sports mode to set
        :param sub_sport_mode: the sub-sport mode to set
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
            reserved,
            sub_sport_mode,
            sport_node,
        )
        return cls(data)
