import logging

import balder

from balderhub.ant.lib.scenario_features.antplus_controller_hrm_feature import AntplusControllerHrmFeature
from balderhub.ant.lib.scenario_features.antplus_hrm_device_config import AntplusHrmDeviceConfig
from balderhub.ant.lib.scenario_features.antplus_hrm_test_criteria_config import AntplusHrmTestCriteriaConfig
from balderhub.ant.lib.scenario_features.heart_rate_monitor_device_profile import HeartRateMonitorDeviceProfile

logger = logging.getLogger(__name__)


class BaseHrmScenario(balder.Scenario):
    """Base test scenario for working with Heart-Rate Monitor devices"""

    class HeartRateSensor(balder.Device):
        """device detecting the row heart rate"""
        ant_config = AntplusHrmDeviceConfig()
        test_criteria = AntplusHrmTestCriteriaConfig()
        hrm = HeartRateMonitorDeviceProfile()

    @balder.connect(HeartRateSensor, over_connection=balder.Connection)  # pylint: disable=undefined-variable
    class HeartRateHost(balder.Device):
        """device receiving the heart rate data"""
        controller = AntplusControllerHrmFeature(AntPlusDevice='HeartRateSensor')
