from __future__ import annotations
from typing import Union

from .base_hrm_page import BaseHrmPage


class Hrm6CapabilitiesPage(BaseHrmPage):
    """
    This is the sixth data page in the HRM profile that holds information about the capabilities within the
    page-specific bytes.
    """
    PAGE_ID = 6
    _STRUCT_DATA_FORMAT = '<BBBBHBB'

    @property
    def feature_supported_byte(self) -> int:
        """
        :return: returns the full byte with the information about which features are supported
        """
        return self._raw_data[2]

    @property
    def feature_enabled_byte(self) -> int:
        """
        :return: returns the full byte with the information about which features are enabled
        """
        return self._raw_data[3]

    def __get_value_for_bit_at_idx(self, idx) -> Union[int, None]:
        if not self.feature_supported_byte & (1 << idx):
            return None
        return bool(self.feature_enabled_byte * (1 << idx))

    @property
    def extended_running_feature_enabled(self) -> Union[bool, None]:
        """
        :return: returns True if the extended-running-feature is enabled, False if it is disabled and None if it is not
                 supported
        """
        return self.__get_value_for_bit_at_idx(0)

    @property
    def extended_cycling_feature_enabled(self) -> Union[bool, None]:
        """
        :return: returns True if the extended-cycling-feature is enabled, False if it is disabled and None if it is not
                 supported
        """
        return self.__get_value_for_bit_at_idx(1)

    @property
    def extended_swimming_feature_enabled(self) -> Union[bool, None]:
        """
        :return: returns True if the extended-swimming-feature is enabled, False if it is disabled and None if it is not
                 supported
        """
        return self.__get_value_for_bit_at_idx(2)

    @property
    def manufacturer_specific_feature_bit6_enabled(self) -> Union[bool, None]:
        """
        :return: returns True if the manufacturer-specific-bit6 is enabled, False if it is disabled and None if it is
                 not supported
        """
        return self.__get_value_for_bit_at_idx(6)

    @property
    def manufacturer_specific_feature_bit7_enabled(self) -> Union[bool, None]:
        """
        :return: returns True if the manufacturer-specific-bit7 is enabled, False if it is disabled and None if it is
                 not supported
        """
        return self.__get_value_for_bit_at_idx(7)
