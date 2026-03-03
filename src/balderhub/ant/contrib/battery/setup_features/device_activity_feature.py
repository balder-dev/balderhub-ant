import balderhub.battery.lib.scenario_features
from balderhub.ant.lib.scenario_features import AntplusControllerHrmFeature


class DeviceActivityFeature(balderhub.battery.lib.scenario_features.DeviceActivityFeature):
    """Setup Level implementation for returning the activity of an ANT device by checking if it sends messages"""

    ant_controller = AntplusControllerHrmFeature()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._channel_was_active_before = None

    @property
    def time_to_wait_for_new_msg_sec(self):
        """
        :return: returns the time in seconds, the feature should wait for a new ant broadcast message
        """
        return 3

    def prepare(self) -> None:
        self._channel_was_active_before = self.ant_controller.channel_is_active
        if not self._channel_was_active_before:
            self.ant_controller.open_channel()

    def cleanup(self) -> None:
        if not self._channel_was_active_before:
            self.ant_controller.close_channel()
            self._channel_was_active_before = None

    def is_active(self) -> bool:
        if self._channel_was_active_before is not None:
            raise ValueError('can not check if ANT is active because this call was not embedded within prepare/cleanup '
                             'calls')
        try:
            self.ant_controller.wait_for_new_broadcast_message(timeout=self.time_to_wait_for_new_msg_sec)
            return True
        except TimeoutError:
            return False
