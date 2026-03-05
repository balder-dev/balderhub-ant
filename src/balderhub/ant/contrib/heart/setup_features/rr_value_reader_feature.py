from typing import Union
import time

import balderhub.heart.lib.scenario_features
from balderhub.ant.lib.scenario_features import AntplusControllerHrmFeature
from balderhub.ant.lib.utils.pages.hrm import BaseHrmPage


class RRValueReaderFeature(balderhub.heart.lib.scenario_features.RRValueReaderFeature):
    """
    Setup Level feature implementation of the ``balderhub.heart.lib.scenario_features.RRValueReaderFeature`` while
    reading the values over ANT
    """
    ant_controller = AntplusControllerHrmFeature()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._channel_was_active_before = None

    @property
    def time_to_wait_for_new_msg_sec(self) -> float:
        """
        :return: returns the time in seconds, the feature should wait for a new ant broadcast message
        """
        return 10.0  # TODO set lower

    def prepare(self):
        self._channel_was_active_before = self.ant_controller.channel_is_active
        if not self._channel_was_active_before:
            self.ant_controller.open_channel()

    def __check_for_channel(self):
        if self._channel_was_active_before is not None:
            raise ValueError('can not check if ANT is active because this call was not embedded within prepare/cleanup '
                             'calls')

    def _msg_has_next_beat(self, msg: BaseHrmPage, msg_before: BaseHrmPage):
        if msg.heart_beat_count == 0:
            return msg_before.heart_beat_count == 255
        return msg_before.heart_beat_count == (msg.heart_beat_count - 1)

    def _calc_rr_value_for(self, msg: BaseHrmPage, msg_before: BaseHrmPage) -> float:
        if not self._msg_has_next_beat(msg, msg_before):
            raise ValueError('can not calculate RR value because previous message has not the expected heart '
                             f'beat count of {msg_before.heart_beat_count} (current has {msg.heart_beat_count})')
        cur_msg_event_time = msg.heart_beat_event_time
        cur_msg_event_time += 0xFFFF if cur_msg_event_time < msg_before.heart_beat_event_time else 0

        return (cur_msg_event_time - msg_before.heart_beat_event_time) / 1024

    def wait_for_next_rr_value_in_sec(self) -> Union[float, None]:
        self.__check_for_channel()
        # first wait for first message
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < self.time_to_wait_for_new_msg_sec:
            if len(self.ant_controller.received_broadcast_messages) > 0:
                # one or more messages here -> break
                break
            time.sleep(self.time_to_wait_for_new_msg_sec / 100)
        else:
            return None
        last_rcvd_msg = self.ant_controller.received_broadcast_messages[-1]

        # now wait for the next one
        while time.perf_counter() - start_time < self.time_to_wait_for_new_msg_sec:
            newest_msg = self.ant_controller.received_broadcast_messages[-1]
            if newest_msg.heart_beat_count != last_rcvd_msg.heart_beat_count:
                # one or more messages here -> break
                if not self._msg_has_next_beat(newest_msg, last_rcvd_msg):
                    raise ValueError(
                        'detect unexpected heart beats for two messages - received new message with heart beat count '
                        f'of {newest_msg.heart_beat_count} (msg before was {last_rcvd_msg.heart_beat_count})'
                    )
                return self._calc_rr_value_for(newest_msg, last_rcvd_msg)
            time.sleep(self.time_to_wait_for_new_msg_sec / 100)
        return None

    def read_last_rr_value_in_sec(self) -> Union[float, None]:
        self.__check_for_channel()

        start_time = time.perf_counter()
        while time.perf_counter() - start_time < self.time_to_wait_for_new_msg_sec:
            if len(set(msg.heart_beat_count for msg in self.ant_controller.received_broadcast_messages)) > 1:
                # more than one messages here -> break
                break
            time.sleep(self.time_to_wait_for_new_msg_sec / 100)
        else:
            return None

        messages = self.ant_controller.received_broadcast_messages
        last_msg = messages[-1]
        heart_beat_count_before = (last_msg.heart_beat_count - 1) % 0x100

        all_msgs = reversed(messages)
        for msg in all_msgs:
            if msg.heart_beat_count not in [heart_beat_count_before, last_msg.heart_beat_count]:
                raise ValueError(f'detect message with unexpected heart beat count of {msg.heart_beat_count} '
                                 f'(current message is {last_msg.heart_beat_count})')
            if msg.heart_beat_count == heart_beat_count_before:
                # get time of message with heart beat before
                return self._calc_rr_value_for(last_msg, msg)
        return None

    def cleanup(self):
        if not self._channel_was_active_before:
            self.ant_controller.close_channel()
            self._channel_was_active_before = None
