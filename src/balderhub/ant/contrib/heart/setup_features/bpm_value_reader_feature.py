import balderhub.heart.lib.scenario_features
from balderhub.ant.lib.scenario_features import AntplusControllerHrmFeature


class BpmValueReaderFeature(balderhub.heart.lib.scenario_features.BpmValueReaderFeature):
    """
    Setup Level feature implementation of the ``balderhub.heart.lib.scenario_features.BpmValueReaderFeature`` while
    reading the values over ANT
    """
    ant_controller = AntplusControllerHrmFeature()

    def read_last_bpm_value(self):
        if not self.ant_controller.channel_is_active:
            self.ant_controller.open_channel()
        return self.ant_controller.wait_for_new_broadcast_message(timeout=1).computed_heart_rate
