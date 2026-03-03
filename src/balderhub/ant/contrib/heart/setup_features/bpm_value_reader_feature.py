import balderhub.heart.lib.scenario_features
from balderhub.ant.lib.scenario_features import AntplusControllerHrmFeature


class BpmValueReaderFeature(balderhub.heart.lib.scenario_features.BpmValueReaderFeature):
    """
    Setup Level feature implementation of the ``balderhub.heart.lib.scenario_features.BpmValueReaderFeature`` while
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
        return 1.0

    def prepare(self):
        self._channel_was_active_before = self.ant_controller.channel_is_active
        if not self._channel_was_active_before:
            self.ant_controller.open_channel()

    def read_last_bpm_value(self):
        if self._channel_was_active_before is not None:
            raise ValueError('can not check if ANT is active because this call was not embedded within prepare/cleanup '
                             'calls')
        new_msg = self.ant_controller.wait_for_new_broadcast_message(timeout=self.time_to_wait_for_new_msg_sec)
        return new_msg.computed_heart_rate

    def cleanup(self):
        if not self._channel_was_active_before:
            self.ant_controller.close_channel()
            self._channel_was_active_before = None
