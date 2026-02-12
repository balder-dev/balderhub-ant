from __future__ import annotations
from typing import Union, OrderedDict, Callable, Generator
import logging

import balder
from balderhub.ant.lib.scenario_features.antplus_device_config import AntplusDeviceConfig
from balderhub.ant.lib.scenario_features.base_antplus_device_profile import BaseAntplusDeviceProfile
from balderhub.ant.lib.utils.page_message_collection import PageMessageCollection
from balderhub.ant.lib.utils.pages import BaseAntplusPage

logger = logging.getLogger(__name__)


class AntplusControllerFeature(balder.Feature):
    """
    Base ANT+ Controller Feature that can be used for any Profile. It holds a inner VDevice that needs to define exactly
    one profile that is based on :class:`BaseAntplusDeviceProfile`.

    This scenario-level feature is used as base class for different type of controllers that are specified for a
    specific profile type.
    """

    class AntPlusDevice(balder.VDevice):
        """vdevice holding the ANT+ device profile"""
        config = AntplusDeviceConfig()
        profile = BaseAntplusDeviceProfile()

    class ValidationError(Exception):
        """error that is raised by internal profile validation functions"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._already_saved_broadcast_messages = PageMessageCollection()
        self._already_saved_ack_messages = PageMessageCollection()
        self._already_saved_burst_messages = PageMessageCollection()

    @property
    def validation_methods(self) -> OrderedDict[str, Callable[[], None]]:
        """
        :return: mapping of validation methods that can be used to check the full validity of all messages sent by a
                 ANT+ device as ordered dict (key is printable name and the callable as value)
        """
        return OrderedDict()

    @property
    def channel_type(self) -> int:  # TODO maybe use own enums
        """
        :return: the own channel type the controller should use
        """
        raise NotImplementedError

    @property
    def rf_channel_frequency(self) -> int:
        """
        :return: the own RF Channel the controller should use
        """
        raise NotImplementedError

    @property
    def transmission_type(self) -> int:  # TODO maybe use own enums
        """
        :return: the own transmission type the controller should use
        """
        raise NotImplementedError

    @property
    def device_type(self) -> int:  # TODO maybe use own enums
        """
        :return: the device type the controller should search for
        """
        raise NotImplementedError

    @property
    def channel_period(self) -> int:
        """
        :return: the channel period the controller should use
        """
        raise NotImplementedError

    @property
    def channel_is_active(self) -> bool:
        """
        :return: returns True if the channel is active, otherwise False
        """
        raise NotImplementedError

    @property
    def received_broadcast_messages(self) -> PageMessageCollection:
        """
        :return: returns the current available BROADCAST messages that has been received since the channel is active
        """
        return self._already_saved_broadcast_messages

    @property
    def received_ack_messages(self) -> PageMessageCollection:
        """
        :return: returns the current available ACK messages that has been received since the channel is active
        """
        return self._already_saved_ack_messages

    # TODO not supported yet
    #@property
    #def received_burst_messages(self) -> PageMessageCollection:
    #    return self._already_saved_burst_messages

    def open_channel(self) -> None:
        """
        Opens the channel
        """
        raise NotImplementedError()

    def close_channel(self) -> None:
        """
        Closes the Channel
        """
        raise NotImplementedError()

    def send_broadcast_message(self, message: BaseAntplusPage) -> None:
        """
        This method sends a given message as BROADCAST message within the open channel
        :param message: the message that should be sent
        """
        raise NotImplementedError()

    def send_ack_message(self, message: BaseAntplusPage) -> None:
        """
        This method sends a given message as ACK message within the open channel
        :param message: the message that should be sent
        """
        raise NotImplementedError()

    def wait_for_new_broadcast_message(
            self,
            of_page_type: Union[list[type[BaseAntplusPage]], type[BaseAntplusPage], None] = None,
            timeout: float = 10
    ) -> BaseAntplusPage:
        """
        This method waits for a new BROADCAST message to be received. All messages that has been received before
        entering this method are not considered.

        If no message is received within the given timeout, the method raises a ``TimeoutError``.

        :param of_page_type: if given, the only considers messages of this specific type
        :param timeout: the maximum time in seconds to wait for a new message
        :return: the new received message
        """
        raise NotImplementedError()

    def wait_for_new_ack_message(
            self,
            of_page_type: Union[list[type[BaseAntplusPage]], type[BaseAntplusPage], None] = None,
            timeout: float = 10
    ) -> BaseAntplusPage:
        """
        This method waits for a new ACK message to be received. All messages that has been received before
        entering this method are not considered.

        If no message is received within the given timeout, the method raises a ``TimeoutError``.

        :param of_page_type: if given, the only considers messages of this specific type
        :param timeout: the maximum time in seconds to wait for a new message
        :return: the new received message
        """
        raise NotImplementedError()

    def get_profile_consistency_validation_report(self) -> OrderedDict[str, Union[str, None]]:
        """
        This method is used to execute a set of validation_functions that makes sure that check that can be applied
        on the raw data of the profile.

        :return: an ordered dict with a description of the validation as key and the error string as value
                 (or None, if sub validation passed)
        """
        result = OrderedDict()
        for cur_descr, cur_callback in self.validation_methods.items():
            try:
                cur_callback()
                result[cur_descr] = None
            except self.ValidationError as exc:
                result[cur_descr] = exc.args[0]
            except Exception as exc:
                raise RuntimeError(f'unexpected error occurred in validation callback `{cur_callback}` '
                                   f'(use ValidationError if it was an validation error)') from exc
        return result

    def validate_profile_consistency(self) -> None:
        """
        This method is used to execute a set of validation_functions that makes sure that check that can be applied
        on the raw data of the profile.
        """
        report = self.get_profile_consistency_validation_report()
        errors = {k:v for k, v in report.items() if v is not None}
        if errors:
            raise ValueError('profile consistency has problems: \n' + '\n'.join(
                [f"- {k}: ERROR MESSAGE `{v}`" for k, v in errors.items()]
            ))

    def _fixt_teardown(self, channel_state_before: bool):
        if channel_state_before:
            if self.channel_is_active:
                logger.info('ANT+ Channel was opened before entering this fixture and it is still opened '
                            '-> do nothing')
            else:
                logger.info('ANT+ Channel was opened before entering this fixture, but it is closed now '
                            '-> open it again')
                self.open_channel()
        else:
            # channel was closed before this fixture
            if self.channel_is_active:
                logger.info('ANT+ Channel was closed before entering this fixture but it is opened now '
                            '-> close it again')
                self.close_channel()
            else:
                logger.info('ANT+ Channel was closed before entering this fixture and it is still closed '
                            '-> do nothing')

    def fixt_make_sure_ant_channel_is_opened(self, restore_entry_state: bool = True) -> Generator[None, None, None]:
        """
        Fixture that makes sure that the ANT Channel is opened. If it is already open when entering this fixture, it
        will do nothing. If it is closed, it will ensure that it is opened as soon as the construction part of this
        fixture is finished.

        .. note::

            You can use this fixture directly by using:

            .. code-block:: python

                @balder.fixture(...)
                def my_fixture(...):
                    yield from feat.fixt_make_sure_ant_channel_is_opened(...)

        :param restore_entry_state: True if the previous state (either open or closed) should be
                                    reestablished in the teardown part of this fixture
        :return: the ready to use fixture generator, but without any values
        """
        channel_was_open = False
        if self.channel_is_active:
            logger.info('ANT+ Channel is already active -> do nothing')
            channel_was_open = True
        else:
            logger.info('ANT+ Channel is inactive -> open it')
            self.open_channel()

        yield None

        if not restore_entry_state:
            return
        self._fixt_teardown(channel_state_before=channel_was_open)

    def fixt_make_sure_ant_channel_is_closed(self, restore_entry_state: bool = True) -> Generator[None, None, None]:
        """
        Fixture that makes sure that the ANT Channel is opened before finishing the construction part of this
        fixture.

        If `restore_entry_state` is True, the method will reestablish the state that was given before entering this
        fixture.

        .. note::

            You can use this fixture directly by using:

            .. code-block:: python

                @balder.fixture(...)
                def my_fixture(...):
                    yield from feat.fixt_make_sure_ant_channel_is_closed(...)

        :param restore_entry_state: True if the previous state (either connected or disconnected) should be
                                    reestablished in the teardown part of this fixture
        :return: the ready to use fixture generator, but without any values
        """
        channel_was_open = False
        if self.channel_is_active:
            logger.info('ANT+ Channel is active -> close it')
            channel_was_open = True
            self.close_channel()
        else:
            logger.info('ANT+ Channel is already inactive -> do nothing')

        yield None

        if not restore_entry_state:
            return
        self._fixt_teardown(channel_state_before=channel_was_open)
