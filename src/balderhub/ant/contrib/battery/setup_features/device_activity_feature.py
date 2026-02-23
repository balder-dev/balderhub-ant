import balderhub.battery.lib.scenario_features
from balderhub.ant.lib.scenario_features import AntplusControllerHrmFeature


class DeviceActivityFeature(balderhub.battery.lib.scenario_features.DeviceActivityFeature):
    """Setup Level implementation for returning the activity of an ANT device by checking if it sends messages"""

    ant_controller = AntplusControllerHrmFeature()

    def is_active(self) -> bool:
        if not self.ant_controller.channel_is_active:
            self.ant_controller.open_channel()
        try:
            self.ant_controller.wait_for_new_broadcast_message(timeout=1)
            return True
        except TimeoutError:
            return False
