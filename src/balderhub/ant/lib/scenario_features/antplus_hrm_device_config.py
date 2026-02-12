# TODO move this in a general available namespace??
from enum import Enum
from typing import Union

from .antplus_device_config import AntplusDeviceConfig
from ..utils import pages


class AntplusHrmDeviceConfig(AntplusDeviceConfig):
    """
    More specific scenario-level device config for devices that implement the HRM profile.
    """

    class SupportedSpecVersion(Enum):
        """enum describing the supported spec version this feature supports"""
        V2_0 = 2.0
        V2_1 = 2.1
        V2_5 = 2.5

    @property
    def supported_spec_version(self) -> SupportedSpecVersion:
        """gives the current supported spec version the device should support"""
        return self.SupportedSpecVersion.V2_5

    @property
    def support_battery_voltage_messuring(self) -> bool:
        """
        :return: returns True if the device supports battery voltage messages within its BatteryLevel Page, otherwise
                 False
        """
        return True

    @property
    def manufacturer_id(self):
        """
        :return: the expected manufacturer ID
        """
        raise NotImplementedError()

    @property
    def serial_number(self):
        """
        :return: the expected serial number of the device
        """
        raise NotImplementedError()

    @property
    def hardware_version(self):
        """
        :return: the expected hardware version of the device
        """
        raise NotImplementedError()

    @property
    def software_version(self):
        """
        :return: the expected software version of the device
        """
        raise NotImplementedError()

    @property
    def model_number(self):
        """
        :return: the expected model number of the device
        """
        raise NotImplementedError()

    @property
    def expected_main_page(
            self
    ) -> Union[type[pages.hrm.Hrm0DefaultDataPage], type[pages.hrm.Hrm4PreviousHeartBeatEventTimePage]]:
        """
        :return: returns the expected MAIN page
        """
        # TODO adjust to sports modes!
        return pages.hrm.Hrm4PreviousHeartBeatEventTimePage

    @property
    def expected_background_pages(
            self
    ) -> list[type[pages.hrm.BaseHrmPage]]:
        """
        :return: returns a list of all pages that are expected to be a BACKGROUND page
        """
        return [
            pages.hrm.Hrm2ManufacturerInformationPage,
            pages.hrm.Hrm3ProductInformationPage,
            pages.hrm.Hrm6CapabilitiesPage,
            pages.hrm.Hrm7BatteryStatusPage,
        ]

    @property
    def manual_request_possible_for(self) -> list[type[pages.hrm.BaseHrmPage]]:
        """
        :return: returns a list of all pages a manual Page-Request (PAGE ID 70) can be done with
        """
        return [
            pages.hrm.Hrm2ManufacturerInformationPage,
            pages.hrm.Hrm3ProductInformationPage,
            pages.hrm.Hrm7BatteryStatusPage,
        ]

    @property
    def manual_request_redirect_ack_as_broadcast(self) -> bool:
        """
        :return: returns True if it is expected that all requested Pages as ACK response are redirected as BROADCAST,
                 False otherwise
        """
        return False

    def get_expected_battery_state_for_level(self, battery_level: int) -> int:
        """
        Converts the given BatteryLevel into the expected Battery-State that is returned withing
        :class:`Hrm7BatteryStatusPage`

        :param battery_level: the battery level to get the expected Battery-State for
        :return: the battery state as integer
        """
        if battery_level == 0:
            return 0x05  # Critical
        if battery_level < 20:
            return 0x04  # Low
        if battery_level < 80:
            return 0x03  # OK
        if battery_level < 90:
            return 0x02 # Good
        return 0x01 # New
