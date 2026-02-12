from typing import Literal, Any
from abc import ABC

import struct


class BaseAntplusPage(ABC):
    """Base Abstract class describing an ANT+ page"""
    PAGE_ID = None # needs to be defined in final page
    _STRUCT_DATA_FORMAT = None
    BYTEORDER: Literal['big', 'little'] = 'little'

    def __init__(
            self,
            raw_data: bytes,
    ):

        if not isinstance(self.__class__.PAGE_ID, int):
            raise TypeError('PAGE_ID must be an integer between 0 and 255')
        if not 0x00 < self.__class__.PAGE_ID <= 0xFF:
            raise ValueError('PAGE_ID must be between 0 and 255')

        if not isinstance(self.__class__._STRUCT_DATA_FORMAT, str):
            raise TypeError('STRUCT_DATA_FORMAT must be a string')

        self._validate_raw_data(raw_data)
        self._validate_page_num(raw_data)

        self._raw_data = raw_data

    def __repr__(self):
        return f"{self.__class__.__name__}<{self._raw_data}>"

    @property
    def raw_data(self) -> bytes:
        """
        :return: the raw data of this page
        """
        return self._raw_data

    def _validate_raw_data(self, for_raw_data: bytes) -> None:
        if not isinstance(for_raw_data, bytes):
            raise TypeError(
                f'raw data must be a bytes object, but is from type {for_raw_data.__class__.__name__}: {for_raw_data}'
            )
        if len(for_raw_data) != 8:
            raise ValueError(f'raw data must be of length 8, but is {len(for_raw_data)} bytes')

    def _validate_page_num(self, in_raw_data: bytes) -> None:
        if in_raw_data[0] != self.PAGE_ID:
            raise ValueError(f'raw data holds wrong page number {in_raw_data[0]} '
                             f'(expected {self.PAGE_ID} for {self.__class__.__name__})')

    def _raw_unpack(self) -> tuple[Any, ...]:
        return struct.unpack(self._STRUCT_DATA_FORMAT, self.raw_data)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.raw_data == other.raw_data

    def __hash__(self):
        return hash(self.raw_data) + hash(self.__class__)
