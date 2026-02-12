import copy


class BaseExtendedMetaLegacy:
    """
    Base class for metadata describing data given by the ANT interface in LEGACY-EXTENDED-DATA message format
    """
    # count of bytes the message has normally (without the flag byte)
    EXPECTED_BYTE_LENGTH = None
    BYTE_ORDER = 'little'

    def __init__(self, raw_data: bytes):
        if not isinstance(raw_data, bytes):
            raise TypeError(f'Expected bytes but got {type(raw_data)}')
        if len(raw_data) != self.EXPECTED_BYTE_LENGTH:
            raise ValueError(f'provided raw data needs to have a length of '
                             f'{self.EXPECTED_BYTE_LENGTH} bytes (is `{raw_data}`)')
        self._raw_data = raw_data

    @property
    def raw_data(self) -> bytes:
        """
        :return: returns the raw bytes that describing the information within this metadata object
        """
        return copy.copy(self._raw_data)
