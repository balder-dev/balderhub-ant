import balder


class AntplusTestCriteriaConfig(balder.Feature):
    """
    General ANT+ test criteria configuration feature
    """

    @property
    def request_transmission_numbers_for_broadcast(self) -> list[int]:
        """
        :return: returns a list of all transmission-numbers that should be tried an validated within
                 :class:`ScenarioHrmManualRequestForBrdcst`
        """
        return [1, 5]

    @property
    def request_transmission_numbers_for_ack(self) -> list[int]:
        """
        :return: returns a list of all transmission-numbers that should be tried an validated within
                 :class:`ScenarioHrmManualRequestForAck`
        """
        return [1, 5]

    @property
    def allowed_packet_loss_percent(self) -> float:
        """value between 0 and 1 that defines the accepted package loss during transmission"""
        return 0

    @property
    def first_number_of_beats_to_skip(self): # TODO improve name
        """
        :return: indicates the number of beat that are ignored before the cyclic values like RR-Value, BPM,
                 consecutive beat counts, ... are validated
        """
        return 0
