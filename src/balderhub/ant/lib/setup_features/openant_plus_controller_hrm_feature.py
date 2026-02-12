import array
import logging
import queue
import time
from typing import Union, Literal

from openant.base.message import Message
from openant.easy.channel import Channel

from .openant_manager_feature import OpenantManagerFeature
from ..scenario_features.antplus_controller_hrm_feature import AntplusControllerHrmFeature
from ..utils.page_message_collection import PageMessageCollection
from ..utils.pages import BaseAntplusPage, BaseReceivedAntplusPage
from ..utils.extended_meta.extended_meta_flagged_channel_id import ExtendedMetaFlaggedChannelId
from ..utils.extended_meta.extended_meta_flagged_rssi import ExtendedMetaFlaggedRssi
from ..utils.extended_meta.extended_meta_flagged_timestamp import ExtendedMetaFlaggedTimestamp
from ..utils.extended_meta.extended_meta_legacy_channel_id import ExtendedMetaLegacyChannelId

logger = logging.getLogger(__name__)


class OpenantPlusControllerHrmFeature(AntplusControllerHrmFeature):
    """
    Setup Level feature implementation for the :class:`AntplusControllerHrmFeature`, by using the
    `openant library <https://github.com/Tigge/openant>`_.
    """

    manager = OpenantManagerFeature()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._openant_channel: Union[Channel, None] = None
        self._broadcast_message_queue = queue.Queue()
        self._ack_message_queue = queue.Queue()
        self._burst_message_queue = queue.Queue()

    @property
    def extended_format(self) -> Literal['legacy', 'flagged', 'none']:
        """
        :return: returns the extended format that should be requested for the ANT channel
        """
        return 'flagged'

    def open_channel(self):
        if self._openant_channel is not None:
            raise ValueError('can not open channel, because another one is still active')

        # reset saved messages TODO
        self._already_saved_broadcast_messages = PageMessageCollection()
        self._already_saved_ack_messages = PageMessageCollection()
        self._already_saved_burst_messages = PageMessageCollection()

        self._openant_channel = self.manager.node.new_channel(self.channel_type, 0x00, 0x01) # TODO configurable?

        # configure callbacks based on if slave or master device

        # configure for MASTER
        self._openant_channel.on_broadcast_data = self._on_broadcast_data
        self._openant_channel.on_burst_data = self._on_burst_data
        self._openant_channel.on_acknowledge_data = self._on_acknowledge
        # only search timeout if slave as searching
        self._openant_channel.set_search_timeout(0xFF)

        self._openant_channel.set_id(self.AntPlusDevice.config.device_num, self.device_type, self.transmission_type)

        self._openant_channel.enable_extended_messages(self.extended_format == 'legacy')

        if self.extended_format == 'legacy':
            self._openant_channel.enable_extended_messages(1)

        if self.extended_format == 'flagged':
            # we will activate everything in flagged mode
            message = Message(Message.ID.LIB_CONFIG, [self._openant_channel.id, 0x80 | 0x20])
            self._openant_channel._ant.write_message(message) # pylint: disable=protected-access

        self._openant_channel.set_period(self.channel_period)
        self._openant_channel.set_rf_freq(self.rf_channel_frequency)

        logger.debug(
            f"opening channel #{self._openant_channel.id}, TYPE 0x{self.channel_type:02x} "
            f"dID {self.AntPlusDevice.config.device_num}; dType {self.device_type}; "
            f"dTrans 0x{self.transmission_type:02x} {self.rf_channel_frequency} @ "
            f"{self.channel_period * 1000 / 0xFFFF:.2f} ms"
        )
        self._openant_channel.open()

    @property
    def channel_is_active(self) -> bool:
        return self._openant_channel and self._openant_channel in self.manager.node.channels

    @property
    def received_broadcast_messages(self) -> PageMessageCollection:
        # read all messages from queue
        msg = self._read_and_save_broadcast_message()

        while msg is not None:
            msg = self._read_and_save_broadcast_message()

        return super().received_broadcast_messages

    @property
    def received_ack_messages(self) -> PageMessageCollection:
        # read all messages from queue
        msg = self._read_and_save_ack_message()

        while msg is not None:
            msg = self._read_and_save_ack_message()

        return super().received_ack_messages

    def get_page_for_no(self, page_no: int) -> type[BaseReceivedAntplusPage]:
        """
        This method returns the page type object for the given page number. It raises a KeyError in case that
        there is no page specified for the given page-number.

        :param page_no: the page number the page type should be returned
        :return: the page type that describes the given page number
        """
        all_hrm_pages = self.AntPlusDevice.profile.get_existing_pages_for_profile()
        if page_no not in all_hrm_pages:
            raise KeyError(f'unable to find page #{page_no}')
        return all_hrm_pages[page_no]

    def _on_broadcast_data(self, data: array.array):
        timestamp = time.perf_counter()
        self._broadcast_message_queue.put((timestamp, data.tobytes()))

    def _on_acknowledge(self, data: array.array):
        timestamp = time.perf_counter()
        self._ack_message_queue.put((timestamp, data.tobytes()))

    def _on_burst_data(self, data: array.array):
        timestamp = time.perf_counter()
        self._burst_message_queue.put((timestamp, data.tobytes()))

    def _get_page_from_raw_data(self, raw_data: bytes) -> type[BaseReceivedAntplusPage]:
        page_no = raw_data[0] & ~(1 << 7)  # on HRM profile -> first bit is toggle bit
        return self.get_page_for_no(page_no)

    @classmethod
    def _parse_legacy_extended_message(
            cls,
            raw_data: bytes
    ) -> list[ExtendedMetaLegacyChannelId]:
        if len(raw_data) != 12:
            raise ValueError(f'expected 12 bytes but for legacy message format {len(raw_data)}')
        return [ExtendedMetaLegacyChannelId(raw_data[0:4])]

    @classmethod
    def _parse_flagged_extended_message(
            cls,
            raw_data: bytes
    ) -> list[Union[ExtendedMetaFlaggedChannelId, ExtendedMetaFlaggedRssi, ExtendedMetaFlaggedTimestamp]]:
        if len(raw_data) <= 8:
            raise ValueError(f'expected more than 8 bytes but for flagged message format {len(raw_data)}')
        extended_data = raw_data[8:]
        all_metas = []
        nxt_idx = 1
        if extended_data[0] & 0x80:
            # next 4 bytes are for `ExtendedMetaLegacyChannelId`
            all_metas.append(ExtendedMetaFlaggedChannelId(extended_data[nxt_idx:nxt_idx + 4]))
            nxt_idx += 4
        if extended_data[0] & 0x40:
            # next 3 bytes are for `ExtendedMetaFlaggedRssi`
            all_metas.append(ExtendedMetaFlaggedRssi(extended_data[nxt_idx:nxt_idx + 3]))
            nxt_idx += 3
        if extended_data[0] & 0x20:
            # next 2 bytes are for `ExtendedMetaFlaggedTimestamp`
            all_metas.append(ExtendedMetaFlaggedTimestamp(extended_data[nxt_idx:nxt_idx + 2]))
            nxt_idx += 2
        if extended_data[nxt_idx:]:
            raise ValueError(f'more extended (flagged) data received than expected: {raw_data}')
        return all_metas

    def _read_from_queue(self, msg_queue: queue.Queue) -> Union[BaseReceivedAntplusPage, None]:
        if msg_queue.empty():
            return None
        timestamp, raw_data = msg_queue.get()

        if self.extended_format == 'none':
            raw_data_of_page_only = raw_data
            meta = None
        elif self.extended_format == 'legacy':
            raw_data_of_page_only = raw_data[4:12]
            meta = self._parse_legacy_extended_message(raw_data)
        elif self.extended_format == 'flagged':
            raw_data_of_page_only = raw_data[0:8]
            meta = self._parse_flagged_extended_message(raw_data)
        else:
            raise ValueError(f'received unexpected value for legacy format `{self.extended_format}`')
        page_type = self._get_page_from_raw_data(raw_data_of_page_only)
        return page_type(raw_data_of_page_only, timestamp=timestamp, extended_metas=meta)

    def _read_and_save_broadcast_message(self) -> Union[BaseAntplusPage, None]:
        msg = self._read_from_queue(self._broadcast_message_queue)
        if msg is None:
            return None
        self._already_saved_broadcast_messages.append(msg)
        return msg

    def _read_and_save_ack_message(self) -> Union[BaseAntplusPage, None]:
        msg = self._read_from_queue(self._ack_message_queue)
        if msg is None:
            return None
        self._already_saved_ack_messages.append(msg)
        return msg

    def send_broadcast_message(self, message: BaseAntplusPage) -> None:
        self._openant_channel.send_broadcast_data(list(message.raw_data))

    def send_ack_message(self, message: BaseAntplusPage):
        self._openant_channel.send_acknowledged_data(list(message.raw_data))

    def close_channel(self) -> bool:
        if self._openant_channel is None:
            return False

        self.manager.node.remove_channel(self._openant_channel)

        # load all messages that are still in queue
        self._read_and_save_broadcast_message()
        self._read_and_save_ack_message()

        self._openant_channel = None
        return True

    def wait_for_new_broadcast_message(
            self,
            of_page_type: Union[list[type[BaseAntplusPage]], type[BaseAntplusPage], None] = None,
            timeout: float = 10
    ) -> BaseAntplusPage:
        # read buffer
        _ = self.received_broadcast_messages

        of_page_type = [of_page_type] if isinstance(of_page_type, type) else of_page_type
        start_time = time.perf_counter()
        while (time.perf_counter() - start_time) < timeout:
            new_msg = self._read_and_save_broadcast_message()
            if new_msg is None:
                time.sleep(0.1)
                continue
            if of_page_type is not None and new_msg.__class__ not in tuple(of_page_type):
                continue
            return new_msg
        raise TimeoutError(f'not received any messages within {timeout} seconds')

    def wait_for_new_ack_message(
            self,
            of_page_type: Union[list[type[BaseAntplusPage]], type[BaseAntplusPage], None] = None,
            timeout: float = 10
    ) -> BaseAntplusPage:
        # read buffer
        _ = self.received_ack_messages

        of_page_type = [of_page_type] if isinstance(of_page_type, type) else of_page_type

        start_time = time.perf_counter()
        while (time.perf_counter() - start_time) < timeout:
            new_msg = self._read_and_save_ack_message()
            if new_msg is None:
                time.sleep(0.1)
                continue
            if of_page_type is not None and new_msg.__class__ not in tuple(of_page_type):
                continue
            return new_msg
        raise TimeoutError(f'not received any messages within {timeout} seconds')
