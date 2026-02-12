from __future__ import annotations

from datetime import timedelta

from .base_hrm_page import BaseHrmPage
from ...page_message_collection import PageMessageCollection


class Hrm1CumulativeOperationTimePage(BaseHrmPage):
    """
    This is the first data page in the HRM profile that holds the cumulative operation time within the page-specific
    bytes.
    """
    PAGE_ID = 1
    _STRUCT_DATA_FORMAT = '<BBBBHBB'

    @property
    def cumulative_operating_time_raw(self) -> int:
        """
        :return: returns the raw cumulative operation time (increments every two seconds)
        """
        return int.from_bytes(self.raw_data[1:4], 'little')

    @property
    def cumulative_operating_time_sec(self) -> int:
        """
        :return: returns the cumulative operation time in seconds
        """
        return self.cumulative_operating_time_raw * 2

    @classmethod
    def validate_messages(
            cls,
            of_msg_collection: PageMessageCollection,
    ) -> None:
        """
        Method to validate the correctness of messages from this type

        :param of_msg_collection: the message collection that should be validated (will automatically be filtered for
                                  messages from :class:`Hrm1CumulativeOperationTimePage`)
        """
        relevant_msgs = of_msg_collection.filter_by_type(page_type=cls)

        # TODO improve validation algorithm
        # counter should increase every two seconds
        if len(relevant_msgs) == 0:
            raise ValueError(f'did not receive any messages for {cls.__name__}')
        assert (relevant_msgs[-1].timestamp - relevant_msgs[0].timestamp) <= timedelta(seconds=2.25), \
            "did not get enough messages to be able to validate Operation-Time counter"

        cleared_optimes = [msg.cumulative_operating_time_raw for msg in relevant_msgs]
        idx_before = 0
        for idx in range(1, len(cleared_optimes)):
            if cleared_optimes[idx_before] <= cleared_optimes[idx]:
                # no overflow -> continue
                continue
            # increase value for all following items
            for sub_idx in range(idx, len(cleared_optimes)):
                cleared_optimes[sub_idx] += 0xFFFFFF
            idx_before = idx

        # determine synchron time
        sync_timestamp = relevant_msgs[0].timestamp
        sync_optime = relevant_msgs[0].cumulative_operating_time_raw

        for idx in range(1, len(relevant_msgs)):
            msg = relevant_msgs[idx]
            diff_timestamp = msg.timestamp - sync_timestamp

            diff_optime_raw = cleared_optimes[idx] - sync_optime
            diff_optime_sec = diff_optime_raw * 2

            # check if difftime is the same (accuracy needs to be around 2 seconds)
            assert diff_optime_sec - 2 < diff_timestamp < diff_optime_sec + 2, \
                f"detect illegal times since message {msg}"
