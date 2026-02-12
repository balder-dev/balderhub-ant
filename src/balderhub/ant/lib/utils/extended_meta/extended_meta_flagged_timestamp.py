from .base_extended_meta_flagged import BaseExtendedMetaFlagged


class ExtendedMetaFlaggedTimestamp(BaseExtendedMetaFlagged):
    """
    Metadata describing data given by the ANT interface in FLAGGED-EXTENDED-DATA message format that describes
    additional TIMESTAMP information
    """
    EXPECTED_BYTE_LENGTH = 2

    @property
    def timestamp_raw(self) -> int:
        """
        :return: returns the raw timestamp value of the message
        """
        return int.from_bytes(self._raw_data, byteorder=self.BYTE_ORDER, signed=False)

    @property
    def timestamp_sec(self) -> float:
        """
        :return: returns the timestamp in seconds (rolls over every two second)
        """
        return self.timestamp_raw / 32768
