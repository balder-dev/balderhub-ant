from __future__ import annotations

from .base_hrm_page import BaseHrmPage
from ...page_message_collection import PageMessageCollection


class Hrm2ManufacturerInformationPage(BaseHrmPage):
    """
    This is the second data page in the HRM profile that holds some manufacturer information within the page-specific
    bytes.
    """
    PAGE_ID = 2
    _STRUCT_DATA_FORMAT = '<BBHHBB'

    @property
    def manufacturer_id(self) -> int:
        """
        :return: returns the manufacturer id of the device
        """
        return self.raw_data[1]

    @property
    def serial_number(self) -> int:
        """
        :return: holds the upper 16 bits of the serial number of the device
        """
        return int.from_bytes(self.raw_data[2:3], 'little')

    @classmethod
    def validate_messages(
            cls,
            of_msg_collection: PageMessageCollection,
            expected_manufacturer_id: int,
            expected_serial_number: int
    ) -> None:
        """
        Method to validate the correctness of messages from this type

        :param of_msg_collection: the message collection that should be validated (will automatically be filtered for
                                  messages from :class:`Hrm2ManufacturerInformationPage`)
        :param expected_manufacturer_id: the expected manufacturer id that should be in all messages of this type
        :param expected_serial_number: the expected serial number that should be in all messages of this type
        """
        relevant_msgs = of_msg_collection.filter_by_type(cls)

        vals_for_manufacturer_id = relevant_msgs.get_unique_values_for_field('manufacturer_id')
        assert len(vals_for_manufacturer_id) == 1 and list(vals_for_manufacturer_id)[0] == expected_manufacturer_id, \
            f"detect unexpected values for `manufacturer_id` for {cls.__name__} messages: `{vals_for_manufacturer_id}`"

        vals_for_serial_number = relevant_msgs.get_unique_values_for_field('serial_number')
        assert len(vals_for_serial_number) == 1 and list(vals_for_serial_number)[0] == expected_serial_number, \
            f"detect unexpected values for `serial_number` for {cls.__name__} messages: `{vals_for_serial_number}`"
