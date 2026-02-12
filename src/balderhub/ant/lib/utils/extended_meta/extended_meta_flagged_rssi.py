from .base_extended_meta_flagged import BaseExtendedMetaFlagged


class ExtendedMetaFlaggedRssi(BaseExtendedMetaFlagged):
    """
    Metadata describing data given by the ANT interface in FLAGGED-EXTENDED-DATA message format that describes
    additional RSSI information
    """
    EXPECTED_BYTE_LENGTH = 3

    @property
    def measurement_type(self) -> int:
        """
        :return: returns the measurement type
        """
        return self._raw_data[0]

    @property
    def rssi(self) -> int:
        """
        :return: returns the current RSSI value
        """
        return int.from_bytes(self._raw_data[1:1], byteorder=self.BYTE_ORDER, signed=True)

    @property
    def threshold_config_value(self) -> int:
        """
        :return: returns the threshold config value
        """
        return int.from_bytes(self._raw_data[2:2], byteorder=self.BYTE_ORDER, signed=True)
