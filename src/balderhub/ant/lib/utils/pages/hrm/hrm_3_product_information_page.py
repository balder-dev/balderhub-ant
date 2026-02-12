from __future__ import annotations
from .base_hrm_page import BaseHrmPage
from ...page_message_collection import PageMessageCollection


class Hrm3ProductInformationPage(BaseHrmPage):
    """
    This is the second data page in the HRM profile that holds some product information within the page-specific
    bytes.
    """
    PAGE_ID = 3
    _STRUCT_DATA_FORMAT = '<BBBBHBB'

    @property
    def hardware_version(self) -> int:
        """
        :return: returns the hardware version of the device
        """
        return self.raw_data[1]

    @property
    def software_version(self) -> int:
        """
        :return: returns the software version of the device
        """
        return self.raw_data[2]

    @property
    def model_number(self) -> int:
        """
        :return: returns the model number of the device
        """
        return self.raw_data[3]

    @classmethod
    def validate_messages(
            cls,
            of_msg_collection: PageMessageCollection,
            expected_hardware_version: int,
            expected_software_version: int,
            expected_model_number: int
    ) -> None:
        """
        Method to validate the correctness of messages from this type

        :param of_msg_collection: the message collection that should be validated (will automatically be filtered for
                                  messages from :class:`Hrm3ProductInformationPage`)
        :param expected_hardware_version: the expected hardware version that should be in all messages of this type
        :param expected_software_version: the expected software version that should be in all messages of this type
        :param expected_model_number: the expected model number that should be in all messages of this type
        :return:
        """
        relevant_msgs = of_msg_collection.filter_by_type(cls)

        vals_for_hwversion = relevant_msgs.get_unique_values_for_field('hardware_version')
        assert len(vals_for_hwversion) == 1 and list(vals_for_hwversion)[0] == expected_hardware_version, \
            f"detect unexpected values for `hardware_version` for {cls.__name__} messages: `{vals_for_hwversion}`"

        vals_for_swversion = relevant_msgs.get_unique_values_for_field('software_version')
        assert len(vals_for_swversion) == 1 and list(vals_for_swversion)[0] == expected_software_version, \
            f"detect unexpected values for `software_version` for {cls.__name__} messages: `{vals_for_swversion}`"

        vals_for_model_number = relevant_msgs.get_unique_values_for_field('model_number')
        assert len(vals_for_model_number) == 1 and list(vals_for_model_number)[0] == expected_model_number, \
            f"detect unexpected values for `model_number` for {cls.__name__} messages: `{vals_for_model_number}`"
