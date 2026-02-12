import time

import balder
from balder.connections import DCPowerConnection

import balderhub.battery.lib.scenario_features
from balderhub.battery.lib.scenario_features import BatteryTestCriteriaConfig

from balderhub.ant.scenarios.hrm.base_hrm_scenario import BaseHrmScenario

from balderhub.ant.lib.utils import pages
from balderhub.heart.lib.scenario_features import HeartBeatFeature, StrapDockingFeature


class ScenarioHrmBatteryMeasuring(BaseHrmScenario):
    """
    Test Scenario validating the sending of the correct battery values when the battery level is changed
    """

    @balder.connect('HeartRateSensor', over_connection=DCPowerConnection)
    class BatterySimulator(balder.Device):
        """device manipulating the battery voltage"""
        sim = balderhub.battery.lib.scenario_features.RemovableBatterySimFeature()

    class Heart(balder.Device):
        """device simulating a heart beat"""
        heart = HeartBeatFeature()

    @balder.connect(Heart, over_connection=balder.Connection)  # pylint: disable=undefined-variable
    class HeartRateSensor(BaseHrmScenario.HeartRateSensor):
        """device detecting the row heart rate"""
        strap = StrapDockingFeature()
        test_config = BatteryTestCriteriaConfig()

    @balder.connect(HeartRateSensor, over_connection=balder.Connection)  # pylint: disable=undefined-variable
    class HeartRateHost(BaseHrmScenario.HeartRateHost):
        """device receiving the heart rate data"""

    @balder.fixture('variation')
    def disconnect_if_necessary(self):
        """fixture that makes sure that current sensor is disconnected"""
        yield from self.HeartRateHost.controller.fixt_make_sure_ant_channel_is_closed(restore_entry_state=True)

    @balder.fixture('variation')
    def heart_beat_established(self, disconnect_if_necessary):  # pylint: disable=unused-argument
        """make sure that heart beat is established, before entering the variation"""
        yield from self.Heart.heart.fixt_make_sure_heart_beat_established(with_bpm=60, restore_entry_state=True)

    @balder.fixture('variation')
    def chest_strap(self, heart_beat_established):  # pylint: disable=unused-argument
        """make sure that the chest strap is attached, before entering the variation"""
        yield from self.HeartRateSensor.strap.fixt_make_sure_to_be_attached(restore_entry_state=True)

    @balder.fixture('variation')
    def power_off_device(self, disconnect_if_necessary, heart_beat_established, chest_strap):  # pylint: disable=unused-argument
        """make sure that the device is powered off, before entering the variation"""
        yield from self.BatterySimulator.sim.fixt_make_sure_device_is_powered_off(restore_entry_state=True)

    @balder.fixture('testcase')
    def wait_for_reset(self, power_off_device):  # pylint: disable=unused-argument
        """wait a second before entering any testcase"""
        time.sleep(1)

    @balder.parametrize_by_feature(
        "battery_level", (HeartRateSensor, 'test_config', 'validation_with_battery_levels')
    )
    def test_check_different_measurements(self, battery_level):
        """
        Test that validates if the different battery levels are presented by the dut while changing them with the
        battery simulator.

        :param battery_level: feature paramized battery level (provided by
                              :meth:`BatteryTestCriteriaConfig.validation_with_battery_levels`)
        """
        self.BatterySimulator.sim.set_to(battery_level)
        expected_voltage = self.BatterySimulator.sim.discharge_characteristic.get_voltage_for(battery_level)
        try:
            self.BatterySimulator.sim.insert_battery()
            try:
                self.HeartRateHost.controller.open_channel()
                data = self.HeartRateHost.controller.wait_for_new_broadcast_message(
                    pages.hrm.Hrm7BatteryStatusPage, timeout=300
                )
                # todo add allowed deviation
                assert data.total_battery_voltage == 3.1, \
                    f"detect unexpected battery voltage {data.total_battery_voltage}V (expected {expected_voltage}V)"
            finally:
                self.HeartRateHost.controller.close_channel()
        finally:
            self.BatterySimulator.sim.remove_battery()
