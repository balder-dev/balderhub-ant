from __future__ import annotations
import logging

import time
from typing import Union, OrderedDict, Callable

try:
    # Python 3.10+
    from typing import TypeAlias
except ImportError:
    # Python < 3.10
    from typing_extensions import TypeAlias

from balderhub.ant.lib.utils import pages

from .antplus_hrm_device_config import AntplusHrmDeviceConfig
from .heart_rate_monitor_device_profile import HeartRateMonitorDeviceProfile
from .antplus_controller_feature import AntplusControllerFeature
from ..utils.support import filter_hrm_messages_by_toggle_bit_change

HrmPagesType: TypeAlias = Union[
    pages.hrm.Hrm0DefaultDataPage,
    pages.hrm.Hrm1CumulativeOperationTimePage,
    pages.hrm.Hrm2ManufacturerInformationPage,
    pages.hrm.Hrm3ProductInformationPage,
    pages.hrm.Hrm4PreviousHeartBeatEventTimePage,
    pages.hrm.Hrm5SwimIntervalSummaryPage,
    pages.hrm.Hrm6CapabilitiesPage,
    pages.hrm.Hrm7BatteryStatusPage,
    pages.hrm.Hrm9DeviceInformationPage,
    pages.hrm.Hrm32HrFeaturePage,
]

logger = logging.getLogger(__name__)


class AntplusControllerHrmFeature(AntplusControllerFeature):
    """
    Special ANT+ controller implementation for the ANT+ Heart-Rate Monitor Profile. The VDevice implements the
    :class:`HeartRateMonitorDeviceProfile`.
    """

    class AntPlusDevice(AntplusControllerFeature.AntPlusDevice):
        """
        inner vdevice representing the ANT+ Device with and implementation of the
        :class:`HeartRateMonitorDeviceProfile`
        """
        config = AntplusHrmDeviceConfig()
        profile = HeartRateMonitorDeviceProfile()

    @property
    def channel_type(self) -> int:  # TODO maybe use own enums
        return 0x00  # Slave

    @property
    def rf_channel_frequency(self) -> int:
        return 0x39  # RF-Channel 57 (2457 MHz)

    @property
    def transmission_type(self) -> int:  # TODO maybe use own enums
        return 0  # for pairing

    @property
    def device_type(self) -> int:  # TODO maybe use own enums
        return 0x78  # specifies Heart-Rate Monitor

    @property
    def channel_period(self) -> int:
        return 8070  # 8070/32769 seconds ~4Hz

    @property
    def channel_is_active(self) -> bool:
        raise NotImplementedError

    def _get_msg_type_count(self, consider_only_toggle_bit_change_msgs: bool = False) -> dict[type[HrmPagesType], int]:
        relevant_messages = self.received_broadcast_messages
        if consider_only_toggle_bit_change_msgs:
            relevant_messages = filter_hrm_messages_by_toggle_bit_change(relevant_messages)

        types_of_messages = [msg.__class__ for msg in relevant_messages]
        type_count = {type: types_of_messages.count(type) for type in set(types_of_messages)}
        self._validate_page_distribution()
        return type_count

    def _get_msg_type_count_for_continues_sequences(self):
        """returns the count of continuous sequences received the same type"""
        result = {}
        last_type = None
        for msg in self.received_broadcast_messages:
            if msg.__class__ == last_type:
                continue
            if msg.__class__ not in result:
                result[msg.__class__] = 0
            result[msg.__class__] = 1
            last_type = msg.__class__
        return result

    def _validate_page_distribution(self):
        """
        Checks if the pages are distributed correctly. By only considering messages with toggle bit change, there need
        to be exactly 16th times more main page messages than background page messages (measurement differences are
        considered - meaning one less is okay).
        :return:
        """

    def determine_main_pages(self) -> list[type[HrmPagesType]]:
        """
        returns the page types of the main pages

        It raises a exception in case there are more than 2 main pages or none main pages
        """
        type_count = self._get_msg_type_count(consider_only_toggle_bit_change_msgs=True)
        max_count = max(type_count.values())
        # all pages that are almost equal to the max count are main pages
        main_pages = [msg_type for msg_type, msg_cnt in type_count.items() if msg_cnt > (max_count - 4)]
        if len(main_pages) == 0:
            raise ValueError(f'not found any main pages, distribution is: {type_count}')
        if len(main_pages) > 2:
            raise ValueError(f'found more than two main pages, distribution is: {type_count}')
        return main_pages

    def determine_background_pages(self) -> list[type[HrmPagesType]]:
        """
        returns the page types of the background pages or None if it is not possible to determine this information with
        the available messages

        It raises a exception in case the internal pattern is definitly wrong.
        """
        main_pages = self.determine_main_pages()

        relevant_continues_sequence_counts = {
            page: cnt for page, cnt in self._get_msg_type_count_for_continues_sequences().items()
            if page not in main_pages
        }

        max_count = max(relevant_continues_sequence_counts.values())
        for cur_page, cur_count in relevant_continues_sequence_counts.items():
            if cur_count < max_count - 1:
                raise ValueError(f'found background page {cur_page} with less than expected '
                                 f'continues-sequence-counts: {relevant_continues_sequence_counts}')

        return list(relevant_continues_sequence_counts.keys())

    def wait_for_new_broadcast_message(
            self,
            of_page_type: type[HrmPagesType] = None,
            timeout: float = 10
    ) -> HrmPagesType:
        start_time = time.perf_counter()
        while (time.perf_counter() - start_time) < timeout:
            messages = self.received_broadcast_messages.filter_by_type(page_type=of_page_type)
            if len(messages) > 0:
                return messages[0]
            time.sleep(0.1)
        raise TimeoutError(f'not received any messages within {timeout} seconds')

    # =============================================== VALIDATION METHODS ===============================================

    @property
    def validation_methods(self) -> OrderedDict[str, Callable[[], None]]:
        meths = super().validation_methods
        meths['Manufacturer Page: Information are valid and have not Changed'] = self.validate_page_2_manufacturer
        meths['Product Page: Information are valid and have not Changed'] = self.validate_page_3_product

        # TODO add more pages (f.e. validate if background page available and so on)
        return meths

    def validate_page_2_manufacturer(self):
        """

        Note that this method raises no error if non message has this message type

        :return:
        """
        # TODO merge with `Hrm2ManufacturerInformationPage.validate`

        page_type = pages.hrm.Hrm2ManufacturerInformationPage

        if page_type not in self.AntPlusDevice.config.expected_background_pages:
            raise self.ValidationError(
                f"your configuration violates the spec: {page_type} needs to be a background page - "
                f"please adjust your `AntplusHrmDeviceConfig.expected_background_pages` setting"
            )

        msgs_of_interest = self.received_broadcast_messages.filter_by_type(page_type=page_type)

        # make sure that data is the same in all messages
        manufacturer_ids = [msg.manufacturer_id for msg in msgs_of_interest]
        if len(set(manufacturer_ids)) > 1:
            raise self.ValidationError(
                f"received different values during session for manufacturer id {set(manufacturer_ids)}"
            )

        if len(manufacturer_ids) > 0 and manufacturer_ids[0] != self.AntPlusDevice.config.manufacturer_id:
            raise self.ValidationError(
                f"unexpected value for manufacturer id: {hex(manufacturer_ids[0])} "
                f"(expected {hex(self.AntPlusDevice.config.manufacturer_id)})"
            )

        serial_numbers = [msg.serial_number for msg in msgs_of_interest]
        if len(set(serial_numbers)) > 1:
            raise self.ValidationError(
                f"received different values during session for serial number {set(serial_numbers)}"
            )

        if len(serial_numbers) > 0 and serial_numbers[0] != self.AntPlusDevice.config.serial_number:
            raise self.ValidationError(
                f"unexpected value for serial_number: {hex(serial_numbers[0])} "
                f"(expected {hex(self.AntPlusDevice.config.serial_number)})")

    def validate_page_3_product(self):
        """

        Note that this method raises no error if non message has this message type

        :return:
        """
        # TODO merge with `Hrm3ManufacturerInformationPage.validate`

        page_type = pages.hrm.Hrm3ProductInformationPage

        if page_type not in self.AntPlusDevice.config.expected_background_pages:
            raise self.ValidationError(
                f"your configuration violates the spec: {page_type} needs to be a background page - "
                f"please adjust your `AntplusHrmDeviceConfig.expected_background_pages` setting"
            )

        msgs_of_interest = self.received_broadcast_messages.filter_by_type(page_type=page_type)

        # make sure that data is the same in all messages
        hardware_versions = [msg.hardware_version for msg in msgs_of_interest]

        if len(set(hardware_versions)) > 1:
            raise self.ValidationError(
                f"received different values during session for hardware_version {set(hardware_versions)}"
            )

        if len(hardware_versions) > 0 and hardware_versions[0] != self.AntPlusDevice.config.hardware_version:
            raise self.ValidationError(
                f"unexpected value for hardware_version: {hex(hardware_versions[0])} "
                f"(expected {hex(self.AntPlusDevice.config.hardware_version)})"
            )

        software_versions = [msg.software_version for msg in msgs_of_interest]

        if len(set(software_versions)) > 1:
            raise self.ValidationError(
                f"received different values during session for software_version {set(software_versions)}"
            )

        if len(software_versions) > 0 and software_versions[0] != self.AntPlusDevice.config.software_version:
            raise self.ValidationError(
                f"unexpected value for software_version: {hex(software_versions[0])} "
                f"(expected {hex(self.AntPlusDevice.config.software_version)})"
            )

        model_numbers = [msg.model_number for msg in msgs_of_interest]

        if len(set(model_numbers)) > 1:
            raise self.ValidationError(
                f"received different values during session for model_numbers {set(model_numbers)}"
            )

        if len(model_numbers) > 0 and model_numbers[0] != self.AntPlusDevice.config.model_number:
            raise self.ValidationError(
                f"unexpected value for model_number: {hex(model_numbers[0])} "
                f"(expected {hex(self.AntPlusDevice.config.model_number)})"
            )
