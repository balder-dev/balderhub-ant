import logging
import threading
from typing import Union

from openant.easy.node import Node

from ..scenario_features.ant_node_manager_feature import AntNodeManagerFeature

logger = logging.getLogger(__name__)


class OpenantManagerFeature(AntNodeManagerFeature):
    """
    Setup Level feature implementation of :class:`balderhub.ant.lib.scenario_features.AntNodeManagerFeature` that uses
    the `OpenAnt Python Library <https://github.com/Tigge/openant>`_ to interact with remote devices
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._thread = None
        self._node = None

    @property
    def node(self) -> Union[Node, None]:
        """
        :return: returns the ``openant.easy.node.Node`` object
        """
        if self._node is None:
            raise ValueError('manager needs to start service before node can be accessed')
        return self._node

    def _threaded_method(self):
        logger.debug('openant manager thread started.')
        self._node.start()

    def start(self):
        self._thread = threading.Thread(target=self._threaded_method)

        self._node = Node()
        self._node.set_network_key(*self.network_and_network_key)

        self._thread.start()

    def shutdown(self, timeout=5) -> bool:
        if self._node is None:
            return False
        self.node.stop()
        self._thread.join(timeout=timeout)
        if self._thread.is_alive():
            raise RuntimeError('manager thread failed to shut down')
        self._node = None
        self._thread = None
        return True
