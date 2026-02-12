import balder

class AntNodeManagerFeature(balder.Feature):
    """
    Base ANT Node Manager Feature - provides bindings to the ANT Stick or the Ant device and manages the connection to
    it. The :class:`AntplusControllerFeature` features use this feature to instantiate their own ANT+ channel.
    """

    @property
    def network_and_network_key(self) -> tuple[int, list[int]]:  # TODO typing
        """
        :return: returns the network and its key the manager should use
        """
        return 0x00, [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

    def start(self) -> None:
        """
        Starts the manager
        """
        raise NotImplementedError()

    def shutdown(self) -> None:
        """
        Shuts down the manager
        """
        raise NotImplementedError()
