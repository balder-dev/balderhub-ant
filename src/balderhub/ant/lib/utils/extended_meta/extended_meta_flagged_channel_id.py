from .base_extended_meta_flagged import BaseExtendedMetaFlagged


class ExtendedMetaFlaggedChannelId(BaseExtendedMetaFlagged):
    """
    Metadata describing data given by the ANT interface in FLAGGED-EXTENDED-DATA message format that describes
    additional Channel ID information
    """
    EXPECTED_BYTE_LENGTH = 4

    @property
    def device_no(self) -> int:
        """
        :return: returns the device number
        """
        return int.from_bytes(self.raw_data[0:1], byteorder=self.BYTE_ORDER, signed=False)

    @property
    def device_type(self) -> int:
        """
        :return: returns the device type
        """
        return self._raw_data[2]

    @property
    def transport_type(self) -> int:
        """
        :return: returns the transport type
        """
        return self._raw_data[3]
