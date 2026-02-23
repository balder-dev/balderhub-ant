import time
from typing import Union


import balderhub.ant.lib.scenario_features
from balderhub.ant.lib.utils import pages
import balderhub.battery.lib.scenario_features


class BatteryLevelReader(balderhub.battery.lib.scenario_features.BatteryLevelReader):
    """Setup Level implementation for reading the battery level over ANT"""
    controller = balderhub.ant.lib.scenario_features.AntplusControllerHrmFeature()

    @property
    def initial_wait_sec(self):
        """
        :return: returns time in seconds to wait for the device to have done the measurement
        """
        return 10

    def read_current_battery_level(self) -> Union[float, None]:
        page = pages.hrm.Hrm7BatteryStatusPage
        request = pages.common.Common70RequestDataPage.create(0x00 | 0x0F, page.PAGE_ID, 0x01)

        channel_was_active_before = self.controller.channel_is_active
        try:
            if not channel_was_active_before:
                self.controller.open_channel()
                time.sleep(self.initial_wait_sec)
            self.controller.send_broadcast_message(request)
            try:
                new_message = self.controller.wait_for_new_broadcast_message(page)
                return new_message.battery_level / 100
            except TimeoutError:
                return None
        finally:
            if not channel_was_active_before:
                self.controller.close_channel()
