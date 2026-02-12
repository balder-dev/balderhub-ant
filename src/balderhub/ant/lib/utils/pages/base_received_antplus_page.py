import time
from typing import Optional, Union, TypeVar

from abc import ABC
from datetime import datetime, timedelta

from balderhub.ant.lib.utils.extended_meta.base_extended_meta_legacy import BaseExtendedMetaLegacy
from balderhub.ant.lib.utils.extended_meta.base_extended_meta_flagged import BaseExtendedMetaFlagged
from .base_antplus_page import BaseAntplusPage

BaseReceivedAntplusPageTypeT = TypeVar('BaseReceivedAntplusPageTypeT', bound='BaseReceivedAntplusPage')


class BaseReceivedAntplusPage(BaseAntplusPage, ABC):
    """
    Base ANT+ Page that is intended to be received from a remote ANT+ device (holds a valid timestamp and metadata)
    """

    def __init__(
            self,
            raw_data: bytes,
            timestamp: float,
            extended_metas: Optional[Union[list[BaseExtendedMetaLegacy], list[BaseExtendedMetaFlagged]]] = None,
    ):

        super().__init__(raw_data=raw_data)

        self._extended_metas = []

        if extended_metas:
            base_class = BaseExtendedMetaFlagged \
                if isinstance(extended_metas[0], BaseExtendedMetaFlagged) \
                else BaseExtendedMetaLegacy

            for meta in extended_metas:
                if not isinstance(meta, base_class):
                    raise TypeError(
                        f'meta objects needs to be either all subclasses of {BaseExtendedMetaLegacy.__name__} '
                        f'or of type {BaseExtendedMetaFlagged.__name__}, '
                    )
                meta_types = [meta.__class__ for meta in extended_metas]
                if len(meta_types) != len(set(meta_types)):
                    raise ValueError('not provide multiple meta objects of same type')
                self._extended_metas.append(meta)

        self._timestamp = timestamp


    def __repr__(self):
        return f"{self.__class__.__name__}<{self._timestamp:.4f}: {self._raw_data}>"

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._timestamp == other._timestamp

    def __hash__(self):
        return hash(self.raw_data) + hash(self.__class__) + hash(self._timestamp)

    @property
    def timestamp(self) -> datetime:
        """
        .. note::
            This is not ment to be a timestamp determined by the ANT host directly. This timestamp is created as soon as
            the message receives the balderhub python implementation.

        :return: returns the timestamp the message was received by the feature
        """
        return datetime.now() - timedelta(seconds=time.perf_counter() - self._timestamp)
