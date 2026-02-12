from __future__ import annotations

import sys
from typing import Iterator, SupportsIndex, Union, Any, TYPE_CHECKING

from datetime import datetime
if TYPE_CHECKING:
    from .pages.base_received_antplus_page import BaseReceivedAntplusPage, BaseReceivedAntplusPageTypeT


class PageMessageCollection:
    """
    Page Message Collection object to manage multiple page messages of the same or different type
    """

    def __init__(self, initial_messages: list[BaseReceivedAntplusPageTypeT] = None):
        self._messages = []

        if initial_messages:
            for msg in initial_messages:
                self.append(msg)

    def __repr__(self):
        return f"{self.__class__.__name__}<{str(self._messages)}>"

    def __iter__(self) -> Iterator[BaseReceivedAntplusPageTypeT]:
        return iter(self._messages)

    def __len__(self):
        return len(self._messages)

    def __getitem__(self, item: int) -> BaseReceivedAntplusPageTypeT:
        return self._messages[item]

    @property
    def messages(self) -> list[BaseReceivedAntplusPageTypeT]:
        """
        :return: returns a copy of all internal messages
        """
        return self._messages.copy()

    def append(self, message: BaseReceivedAntplusPageTypeT) -> None:
        """
        Adds a message to the collection. It will be automatically inserted in the correct order according to its
        timestamp.

        :param message: the message that should be added to the collection
        """
        from .pages.base_received_antplus_page import BaseReceivedAntplusPage  # pylint: disable=import-outside-toplevel

        if not isinstance(message, BaseReceivedAntplusPage):
            raise TypeError(f'messages need to be a subclass of type {BaseReceivedAntplusPage}')

        self._messages.append(message)

        self._sort_by_timestamp()

    def index(
            self,
            value: BaseReceivedAntplusPageTypeT,
            start: SupportsIndex = 0,
            stop: SupportsIndex = sys.maxsize
    ) -> int:
        """
        Returns the index of the next (similar to ``list.index``)

        :param value: the value to look for
        :param start: first index to look at
        :param stop: last index to look at
        :return: the index within the internal messsage list
        """
        return self._messages.index(value, start, stop)

    def _sort_by_timestamp(self):
        self._messages.sort(key=lambda x: x.timestamp)

    def filter_by_type(
            self,
            page_type: type[BaseReceivedAntplusPageTypeT]
    ) -> PageMessageCollection[BaseReceivedAntplusPageTypeT]:
        """
        Returns a new collection that holds all messages from the given type

        :param page_type: the page type to filter this message collection
        :return: a new collection that holds all messages from the given type
        """
        result = self.__class__()
        for msg in self._messages:
            if msg.__class__ == page_type:
                result.append(msg)
        return result

    def get_unique_values_for_field(
            self,
            field_name: str,
            ignore_non_existing=False
    ) -> set[Any]:
        """
        This method returns a set of values the messages within this collection has. If ``ignore_non_existing`` is False
        the method will raise an exception if there is a message type that does not provide the ``field_name`` as
        property.

        :param field_name: the field name the unique value set should be returned for
        :param ignore_non_existing: True if all messages that does not have this field are ignored, False otherwise
                                    (raises an error)
        :return: the unique set of values that exist within this collection
        """
        all_values = set()
        for msg in self._messages:
            if ignore_non_existing:
                if hasattr(msg, field_name):
                    all_values.add(getattr(msg, field_name))
            else:
                all_values.add(getattr(msg, field_name))
        return all_values

    def get_unique_value_for_field(self, field_name: str) -> Any | None:
        """
        This method returns the unique value for one field. It throws an error if the method finds more than one values
        or if the field does not exist within one or more messages.
        :param field_name:
        :return:
        """
        all_unique_vals = self.get_unique_values_for_field(field_name)
        if len(all_unique_vals) == 1:
            return all_unique_vals.pop()
        raise ValueError('found multiple values for field name `{}` within messages')

    def get_first_message(
            self,
            of_page_type: Union[type[BaseReceivedAntplusPageTypeT], None]
    ) -> Union[BaseReceivedAntplusPageTypeT, None]:
        """
        This method returns the first occurrence of the given page-type within this collection.

        :param of_page_type: the page type to look for
        :return: the first page-message of the requested type that is within this collection or None if no message of
                 this type was found
        """
        filtered = self if of_page_type is None else self.filter_by_type(page_type=of_page_type)
        return filtered[0]

    def get_last_message(
            self,
            of_page_type: Union[type[BaseReceivedAntplusPageTypeT], None]
    ) -> Union[BaseReceivedAntplusPageTypeT, None]:
        """
        This method returns the last occurrence of the given page-type within this collection.

        :param of_page_type: the page type to look for
        :return: the last page-message of the requested type that is within this collection or None if no message of
                 this type was found
        """
        filtered = self if of_page_type is None else self.filter_by_type(page_type=of_page_type)
        return filtered[-1]

    def get_message_types(self) -> set[type[BaseReceivedAntplusPageTypeT]]:
        """
        :return: returns a set object of all page-message types that exist within this collection
        """
        return set(msg.__class__ for msg in self._messages)

    def filter_for_timestamp(
            self,
            start: datetime = None,
            end: datetime = None
    ) -> PageMessageCollection[BaseReceivedAntplusPageTypeT]:
        """
        This method returns all messages which timestamp is between the given start and/or end date
        :param start: start (exclusive) timestamp, the messages can have to be returned
        :param end: end (exclusive) timestamp, the messages can have to be returned
        :return: a new collection that matches the given filter criteria
        """
        result = self.__class__()

        for msg in self._messages:
            if start is not None and msg.timestamp < start:
                continue
            if end is not None and msg.timestamp > end:
                continue
            result.append(msg)
        return result
