import balder


class AntplusDeviceConfig(balder.Feature):
    """Base universal ANT+ Device configuration feature"""

    @property
    def device_num(self):
        """
        :return: returns the device number of the device
        """
        raise NotImplementedError()
