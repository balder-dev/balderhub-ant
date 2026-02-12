from .base_antplus_device_profile import BaseAntplusDeviceProfile
from ...lib.utils import pages


class HeartRateMonitorDeviceProfile(BaseAntplusDeviceProfile):
    """
    This feature can be assigned to an ANT+ device that supports the Heart Rate Monitor profile.
    """

    ALL_PAGES = [
        pages.hrm.Hrm0DefaultDataPage,
        pages.hrm.Hrm1CumulativeOperationTimePage,
        pages.hrm.Hrm2ManufacturerInformationPage,
        pages.hrm.Hrm3ProductInformationPage,
        pages.hrm.Hrm4PreviousHeartBeatEventTimePage,
        pages.hrm.Hrm5SwimIntervalSummaryPage,
        pages.hrm.Hrm6CapabilitiesPage,
        pages.hrm.Hrm7BatteryStatusPage,
        pages.hrm.Hrm9DeviceInformationPage,
    ]
