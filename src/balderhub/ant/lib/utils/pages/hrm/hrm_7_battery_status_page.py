from __future__ import annotations

from typing import Union

from .base_hrm_page import BaseHrmPage
from ...page_message_collection import PageMessageCollection


class Hrm7BatteryStatusPage(BaseHrmPage):
    """
    This is the seventh data page in the HRM profile that holds information about the battery within the page-specific
    bytes.
    """
    PAGE_ID = 7
    _STRUCT_DATA_FORMAT = '<BBBBHBB'

    @property
    def battery_level(self) -> int:
        """
        :return: returns the battery level
        """
        return self._raw_data[1]

    @property
    def fractional_battery_voltage(self) -> int:
        """
        :return: returns the raw fractional battery voltage if given (use
                 :meth:`Hrm7BatteryStatusPage.total_battery_voltage` for the full voltage information)
        """
        return self._raw_data[2]

    @property
    def descriptive_bit_field(self) -> int:
        """
        :return: returns the full raw descriptive bit field
        """
        return self._raw_data[3]

    @property
    def coarse_battery_voltage(self) -> int:
        """
        :return: returns the coarse battery voltage value
        """
        return self.descriptive_bit_field & 0xF

    @property
    def battery_status(self) -> int:
        """
        :return: returns the battery status value
        """
        return (self.descriptive_bit_field & 0x70) >> 4

    @property
    def total_battery_voltage(self) -> Union[float, None]:
        """
        :return: returns the full battery voltage value or None if it is marked as invalid
        """
        if self.coarse_battery_voltage == 0xF:
            return None
        return (self.descriptive_bit_field & 0x0F) + (self.fractional_battery_voltage / 255)

    @classmethod
    def validate_messages(
            cls,
            of_msg_collection: PageMessageCollection,
            expected_battery_level: int,
            expected_battery_status: Union[int, None],
            expected_battery_voltage: Union[float, None],
            allowed_deviation_for_battery_voltage_percent: float = 0.0
    ) -> None:
        """
        Method to validate the correctness of messages from this type

        Note that with this check all Battery messages within the provided collection need to have the same value.
        Split it by yourself in case you need to validate different values.


        :param of_msg_collection: the message collection that should be validated (will automatically be filtered for
                                  messages from :class:`Hrm7BatteryStatusPage`)
        :param expected_battery_level: the expected battery level that should be in all messages of this type
        :param expected_battery_status: the expected battery status that should be in all messages of this type or None,
                                        if it is expected that the device sends INVALID (0xF) here
        :param expected_battery_voltage: the expected battery voltage that should be in all messages of this type or
                                         None, if it is expected that the device sends INVALID (0xF in coarse voltage)
                                         here
        """
        relevant_msgs = of_msg_collection.filter_by_type(page_type=cls)

        vals_for_battery_level = list(relevant_msgs.get_unique_values_for_field('battery_level'))
        assert len(vals_for_battery_level) == 1 and vals_for_battery_level[0] == expected_battery_level, \
            (f"detect unexpected values for `battery_level` for {cls.__name__} messages: `{vals_for_battery_level}` "
             f"(expected {expected_battery_level})")
        assert 0 <= vals_for_battery_level[0] <= 100, \
            f"battery level is not in expected range of 0-100, is {vals_for_battery_level[0]}"

        if expected_battery_voltage:
            vals_for_bat_voltage = list(relevant_msgs.get_unique_values_for_field('total_battery_voltage'))
            assert len(vals_for_bat_voltage) == 1, \
                (f"detect unexpected count of values for `total_battery_voltage` for {cls.__name__} messages: "
                 f"`{vals_for_bat_voltage}`")

            min_expected_voltage = expected_battery_voltage * (1 - allowed_deviation_for_battery_voltage_percent)
            max_expected_voltage = expected_battery_voltage * (1 + allowed_deviation_for_battery_voltage_percent)
            assert min_expected_voltage <= vals_for_bat_voltage[0] <= max_expected_voltage, \
                (f"battery voltage of {vals_for_bat_voltage[0]} is not in expected range "
                 f"(expected voltage is {expected_battery_voltage} "
                 f"+/- {allowed_deviation_for_battery_voltage_percent*100:.2f}%: "
                 f"{min_expected_voltage:.3f}V - {max_expected_voltage:.3f}V)")

            val_for_coarse_voltage = list(relevant_msgs.get_unique_values_for_field('coarse_battery_voltage'))
            assert len(val_for_coarse_voltage) == 1, (f"detect unexpected values for `coarse_battery_voltage` for "
                                                      f"{cls.__name__} messages: `{vals_for_bat_voltage}`")
            assert 0 < val_for_coarse_voltage[0] < 0xF, \
                f"coarse_battery_voltage has invalid value {val_for_coarse_voltage}"
        else:
            # battery voltage is expected to be set to INVALID
            fractional_battery_voltage = relevant_msgs.get_unique_value_for_field('fractional_battery_voltage')
            assert fractional_battery_voltage == 0xFF, ("fractional battery voltage should be set to 0xFF, because "
                                                        "it's expected that the battery voltage is transmitted as "
                                                        "INVALID")

            coarse_voltage = relevant_msgs.get_unique_value_for_field('coarse_battery_voltage')
            assert coarse_voltage == 0xF, ("coarse battery voltage within descriptive bit field should be set to 0xF, "
                                           "because it's expected that the battery voltage is transmitted as INVALID")

        val_for_bat_status = relevant_msgs.get_unique_value_for_field('battery_status')
        if expected_battery_status:
            assert 0x00 < val_for_bat_status < 0x07, \
                f"battery status for message has invalid value {val_for_bat_status}"

            assert val_for_bat_status == expected_battery_status, \
                (f"detect unexpected values for `battery_status` for {cls.__name__} messages: `{val_for_bat_status}`"
                 f" (expected {expected_battery_status})")

        else:
            assert val_for_bat_status == 0x07, \
                f"battery status for message does not have expected invalid value {val_for_bat_status}"
