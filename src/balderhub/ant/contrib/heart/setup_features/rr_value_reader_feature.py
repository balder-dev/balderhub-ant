import time

import balderhub.heart.lib.scenario_features
from balderhub.ant.lib.scenario_features import AntplusControllerHrmFeature


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
        return 3.0

    def prepare(self):
        self._channel_was_active_before = self.ant_controller.channel_is_active
        if not self._channel_was_active_before:
            self.ant_controller.open_channel()

    def read_last_rr_value_in_sec(self) -> float:
        # TODO optimize
        if self._channel_was_active_before is not None:
            raise ValueError('can not check if ANT is active because this call was not embedded within prepare/cleanup '
                             'calls')

        start_time = time.perf_counter()
        while time.perf_counter() - start_time < self.time_to_wait_for_new_msg_sec:
            cur_msg = self.ant_controller.wait_for_new_broadcast_message(timeout=1)
            if len(set(msg.heart_beat_count for msg in self.ant_controller.received_broadcast_messages)) > 1:
                # more than one messages here -> break
                break
        else:
            raise TimeoutError(f'did not received more than one heart beat messages within '
                               f'{self.time_to_wait_for_new_msg_sec} seconds')

        heart_beat_count_before = cur_msg.heart_beat_count

        all_msgs = reversed(self.ant_controller.received_broadcast_messages.messages)
        for msg in all_msgs:
            if msg.heart_beat_count not in [heart_beat_count_before, cur_msg.heart_beat_count]:
                raise ValueError(f'detect message with unexpected heart beat count of {msg.heart_beat_count} '
                                 f'(current message is {cur_msg.heart_beat_count})')
            if msg.heart_beat_count == heart_beat_count_before:
                cur_msg_event_time = cur_msg.heart_beat_event_time
                cur_msg_event_time += 0xFFFF if cur_msg_event_time < msg.heart_beat_event_time else 0

                return (msg.heart_beat_event_time - cur_msg_event_time) / 1024
        raise ValueError('was unable to detect a correct previous heart beat message')

    def cleanup(self):
        if not self._channel_was_active_before:
            self.ant_controller.close_channel()
            self._channel_was_active_before = None
