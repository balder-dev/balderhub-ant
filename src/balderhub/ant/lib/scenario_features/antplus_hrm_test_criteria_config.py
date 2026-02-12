from .antplus_test_criteria_config import AntplusTestCriteriaConfig


class AntplusHrmTestCriteriaConfig(AntplusTestCriteriaConfig):
    """
    Heart-Rate-Monitor specific ANT+ test criteria configuration feature
    """

    def get_allowed_min_max_rr_value_for(self, expected_rr_value_sec: float) -> tuple[float, float]:
        """
        This method returns the allowed min and max value for a given RR-Value within a heart-rate monitor profile
        :param expected_rr_value_sec: the expected value of the RR-Value
        :return: a tuple with the min and the max allowed values the real RR-Value is allowed to have
        """
        return expected_rr_value_sec * 0.9, expected_rr_value_sec * 1.1

    def get_allowed_min_max_bpm_value_for(self, expected_bpm_value: int) -> tuple[int, int]:
        """
        This method returns the allowed min and max value for a given BPM value within a heart-rate monitor profile
        :param expected_bpm_value: the expected value of the BPM
        :return: a tuple with the min and the max allowed values the real BPM is allowed to have
        """
        return max(0, expected_bpm_value - 1), expected_bpm_value + 1
