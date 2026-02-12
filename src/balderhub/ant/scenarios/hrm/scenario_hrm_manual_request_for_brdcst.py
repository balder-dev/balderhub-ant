import time
from datetime import datetime, timedelta
import logging

import balder
from balder.connections import DCPowerConnection

from balderhub.ant.lib.utils import pages
import balderhub.battery.lib.scenario_features
from balderhub.heart.lib.scenario_features import HeartBeatFeature, StrapDockingFeature

from .base_hrm_scenario import BaseHrmScenario
from ...lib.utils.page_message_collection import PageMessageCollection

logger = logging.getLogger(__name__)


class ScenarioHrmManualRequestForBrdcst(BaseHrmScenario):
    """
    Test scenario for validating the correct responses when sending a :class:`Common70RequestDataPage` and ask for
    BROADCAST messages as response. This scenario tests every possible background page and expects that the HR-Sensor
    responses with an BROADCAST message as answer. It also validates its content.

    In case the page is not mentioned within :meth:`AntplusHrmDeviceConfig.manual_request_possible_for`, the tests
    within this scenario expect that the DUT does not respond with the requested page. Instead, it just continues its
    usual messages without sending anything as ACK.
    """

    # TODO further test ideas: wait till we expect exactly the background page and then request it (new scenario)
    # TODO further test idea: request a page (transmission-count = 100) and directly after that ask for another one
    # TODO also check the illegal value for request-transmission-response: 0x00 (problems?)
    # TODO it would be also interesting if we do the test before the normal timeslot of a background page
    # TODO can I request another page after I've tried to request an invalid Common Page?

    DO_WITH_BATTERY_LEVEL = 1.0
    ADDITIONAL_WAIT_SEC = 5


    class Heart(balder.Device):
        """heart beat simulating device"""
        heart = HeartBeatFeature()

    @balder.connect('HeartRateSensor', over_connection=DCPowerConnection)
    class BatterySimulator(balder.Device):
        """device manipulating the battery voltage"""
        sim = balderhub.battery.lib.scenario_features.RemovableBatterySimFeature()

    @balder.connect(Heart, over_connection=balder.Connection)  # pylint: disable=undefined-variable
    class HeartRateSensor(BaseHrmScenario.HeartRateSensor):
        """device detecting the row heart rate"""
        strap = StrapDockingFeature()

    @balder.connect(HeartRateSensor, over_connection=balder.Connection)  # pylint: disable=undefined-variable
    class HeartRateHost(BaseHrmScenario.HeartRateHost):
        """device receiving the heart rate data"""

    @balder.fixture('variation')
    def device_powered_on(self):
        """fixture that ensures that the device is powered on, before entering the variation"""
        yield from self.BatterySimulator.sim.fixt_make_sure_device_is_powered_on(
            with_level=self.DO_WITH_BATTERY_LEVEL,
            restore_entry_state=True
        )

    @balder.fixture('variation')
    def heart_beat_established(self, device_powered_on):  # pylint: disable=unused-argument
        """fixture that ensures that the heart beat is active, before entering the variation"""
        yield from self.Heart.heart.fixt_make_sure_heart_beat_established(with_bpm=60, restore_entry_state=True)

    @balder.fixture('variation')
    def chest_strap_attached(self, heart_beat_established):  # pylint: disable=unused-argument
        """fixture that ensures that the chest strap is attached, before entering the variation"""
        yield from self.HeartRateSensor.strap.fixt_make_sure_to_be_attached(restore_entry_state=True)

    @balder.fixture('variation')
    def ant_connected(self, chest_strap_attached):  # pylint: disable=unused-argument
        """fixture that ensures that ANT channel is open, before entering the variation"""
        yield from self.HeartRateHost.controller.fixt_make_sure_ant_channel_is_opened()

    @classmethod
    def get_page_to_send(
            cls,
            page_to_request: type[pages.hrm.BaseHrmPage],
            transmit_no: int
    ) -> pages.common.Common70RequestDataPage:
        """
        Helper method to get the Request-Data-Page object filled with the given data

        :param page_to_request: the page that should be requested
        :param transmit_no: the requested transmit number
        :return: the filled and ready to send request-page
        """
        assert 0 < transmit_no <= 0x7F, f"illegal value for transmit_no: {transmit_no}"
        return pages.common.Common70RequestDataPage.create(0x00 | transmit_no, page_to_request.PAGE_ID, 0x01)

    def _do_request_for_brdcst(
            self,
            page_to_request: type[pages.hrm.BaseHrmPage],
            transmit_no: int
    ) -> PageMessageCollection:
        page_to_send = self.__class__.get_page_to_send(page_to_request=page_to_request, transmit_no=transmit_no)

        # do sync and wait for the first background page to be fully transmitted - does not matter which background page
        self.HeartRateHost.controller.wait_for_new_broadcast_message(
            of_page_type=self.HeartRateSensor.ant_config.expected_background_pages,
            timeout=20  # increase timeout because 64 / 4 ~ 16 second
        )
        self.HeartRateHost.controller.wait_for_new_broadcast_message(
            of_page_type=self.HeartRateSensor.ant_config.expected_main_page
        )
        # after background page was fully transmitted -> send request (now it should normally return main pages)
        timestamp_before = datetime.now()
        self.HeartRateHost.controller.send_broadcast_message(page_to_send)

        # wait for all messages to be transmitted (with some additional seconds - we want to check that it continues
        #  with main pages after that)
        time.sleep(max(1, transmit_no) * 0.25 + self.ADDITIONAL_WAIT_SEC)
        # make sure that we did not receive any ACK messages
        relevant_ack_msgs = self.HeartRateHost.controller.received_ack_messages.filter_for_timestamp(
            start=timestamp_before
        )
        assert len(relevant_ack_msgs) == 0, \
            f"received some unexpected ACK messages during timeslot: {relevant_ack_msgs}"

        relevant_brdcst_msgs = self.HeartRateHost.controller.received_broadcast_messages.filter_for_timestamp(
            start=timestamp_before
        )

        # make sure that we received exactly the transmit-no count of messages
        # TODO this needs to cleaned up for message-loss
        msgs_of_requested_page_type = relevant_brdcst_msgs.filter_by_type(page_type=page_to_request)

        assert len(msgs_of_requested_page_type) == transmit_no, \
            (f"received unexpected count of messages - received {len(msgs_of_requested_page_type)} messages of "
             f"type {page_to_request.__name__}, but expected length was {transmit_no}")

        first_msg = msgs_of_requested_page_type[0]
        last_msg = msgs_of_requested_page_type[-1]

        # check Request-Page Message response time (time between request and first response)
        # TODO this needs to cleaned up for message-loss
        assert (first_msg.timestamp - timestamp_before) < timedelta(seconds=1), \
            "response time is higher than expected" # TODO make configurable


        # make sure that we only received main pages afterwards
        remaining_msgs = relevant_brdcst_msgs.filter_for_timestamp(start=last_msg.timestamp + timedelta(seconds=0.1))

        assert len(remaining_msgs) > 0, ("expect some more main page messages after last transferred requested page "
                                         "messages, but did not receive anything more")

        all_msg_types = list(remaining_msgs.get_message_types())
        assert (len(all_msg_types) == 1 and all_msg_types[0] == self.HeartRateSensor.ant_config.expected_main_page), \
            (f"received messages from unexpected type (only main pages were expected after all responses for Page 70 "
             f"Request have been transmitted): {remaining_msgs}")

        return msgs_of_requested_page_type

    def _do_request_for_brdcst_but_expect_no_response(
            self,
            page_to_request: type[pages.hrm.BaseHrmPage],
            transmit_no: int
    ) -> None:
        page_to_send = self.__class__.get_page_to_send(page_to_request=page_to_request, transmit_no=transmit_no)

        # do sync and wait for the first background page to be fully transmitted - does not matter which background page
        self.HeartRateHost.controller.wait_for_new_broadcast_message(
            of_page_type=self.HeartRateSensor.ant_config.expected_background_pages,
            timeout=20  # increase timeout because 64 / 4 ~ 16 second
        )
        self.HeartRateHost.controller.wait_for_new_broadcast_message(
            of_page_type=self.HeartRateSensor.ant_config.expected_main_page
        )

        # after background page was fully transmitted -> send request (now it should normally return main pages)
        timestamp_before = datetime.now()
        self.HeartRateHost.controller.send_broadcast_message(page_to_send)
        # wait for all messages to be transmitted (with some additional seconds - we want to make sure that no pages
        # has been transmitted)
        time.sleep(max(1, transmit_no) * 0.25 + self.ADDITIONAL_WAIT_SEC)
        # make sure that we did not receive any ACK messages
        relevant_ack_msgs = self.HeartRateHost.controller.received_ack_messages.filter_for_timestamp(
            start=timestamp_before
        )
        assert len(relevant_ack_msgs) == 0, \
            f"received some unexpected ACK messages during timeslot: {relevant_ack_msgs}"

        relevant_brdcst_msgs = self.HeartRateHost.controller.received_broadcast_messages.filter_for_timestamp(
            start=timestamp_before
        )

        # make sure that we have only received main pages
        msg_types = relevant_brdcst_msgs.get_message_types()
        assert len(msg_types) == 1 and list(msg_types)[0] == self.HeartRateSensor.ant_config.expected_main_page, \
            (f"received unexpected broadcast messages while requesting a non-active page "
             f"{page_to_request.__name__}: {msg_types}")

    @balder.parametrize_by_feature(
        'transmit_no', (HeartRateSensor, 'test_criteria', 'request_transmission_numbers_for_broadcast')
    )
    def test_brdcst_page_1_operating_time(self, transmit_no: int):
        """
        Test that validates the correct behavior, when the controller ask for a BROADCAST message of
        :class:`Hrm1CumulativeOperationTimePage`. The test validates that the DUT answers the correct count of requested
        messages, when the page is mentioned in :meth:`AntplusHrmDeviceConfig.manual_request_possible_for`. Otherwise,
        it will ensure that the DUT ignores the request.

        If the test expects a response it will also validate the content of the messages. Additionally, it makes sure
        that no messages are sent as ACK because it requests BROADCAST messages only.

        :param transmit_no: PARAMETRIZED value describing the requested times the message should be sent
        """
        page_type = pages.hrm.Hrm1CumulativeOperationTimePage

        if page_type in self.HeartRateSensor.ant_config.manual_request_possible_for:
            response = self._do_request_for_brdcst(page_type, transmit_no)

            page_type.validate_messages(
                of_msg_collection=response,
            )
        else:
            self._do_request_for_brdcst_but_expect_no_response(page_type, transmit_no)

    @balder.parametrize_by_feature(
        'transmit_no', (HeartRateSensor, 'test_criteria', 'request_transmission_numbers_for_broadcast')
    )
    def test_brdcst_page_2_manufacturer(self, transmit_no: int):
        """
        Test that validates the correct behavior, when the controller ask for a BROADCAST message of
        :class:`Hrm2ManufacturerInformationPage`. The test validates that the DUT answers the correct count of requested
        messages, when the page is mentioned in :meth:`AntplusHrmDeviceConfig.manual_request_possible_for`. Otherwise,
        it will ensure that the DUT ignores the request.

        If the test expects a response it will also validate the content of the messages. Additionally, it makes sure
        that no messages are sent as ACK because it requests BROADCAST messages only.

        :param transmit_no: PARAMETRIZED value describing the requested times the message should be sent
        """
        page_type = pages.hrm.Hrm2ManufacturerInformationPage

        if page_type in self.HeartRateSensor.ant_config.manual_request_possible_for:
            response = self._do_request_for_brdcst(page_type, transmit_no)

            page_type.validate_messages(
                of_msg_collection=response,
                expected_manufacturer_id=self.HeartRateSensor.ant_config.manufacturer_id,
                expected_serial_number=self.HeartRateSensor.ant_config.serial_number
            )
        else:
            self._do_request_for_brdcst_but_expect_no_response(page_type, transmit_no)

    @balder.parametrize_by_feature(
        'transmit_no', (HeartRateSensor, 'test_criteria', 'request_transmission_numbers_for_broadcast')
    )
    def test_brdcst_page_3_product(self, transmit_no: int):
        """
        Test that validates the correct behavior, when the controller ask for a BROADCAST message of
        :class:`Hrm3ProductInformationPage`. The test validates that the DUT answers the correct count of requested
        messages, when the page is mentioned in :meth:`AntplusHrmDeviceConfig.manual_request_possible_for`. Otherwise,
        it will ensure that the DUT ignores the request.

        If the test expects a response it will also validate the content of the messages. Additionally, it makes sure
        that no messages are sent as ACK because it requests BROADCAST messages only.

        :param transmit_no: PARAMETRIZED value describing the requested times the message should be sent
        """
        page_type = pages.hrm.Hrm3ProductInformationPage

        if page_type in self.HeartRateSensor.ant_config.manual_request_possible_for:
            response = self._do_request_for_brdcst(page_type, transmit_no)

            page_type.validate_messages(
                of_msg_collection=response,
                expected_hardware_version=self.HeartRateSensor.ant_config.hardware_version,
                expected_software_version=self.HeartRateSensor.ant_config.software_version,
                expected_model_number=self.HeartRateSensor.ant_config.model_number,
            )
        else:
            self._do_request_for_brdcst_but_expect_no_response(page_type, transmit_no)

    @balder.parametrize_by_feature(
        'transmit_no', (HeartRateSensor, 'test_criteria', 'request_transmission_numbers_for_broadcast')
    )
    def test_brdcst_page_6_capabilities(self, transmit_no: int):
        """
        Test that validates the correct behavior, when the controller ask for a BROADCAST message of
        :class:`Hrm6CapabilitiesPage`. The test validates that the DUT answers the correct count of requested
        messages, when the page is mentioned in :meth:`AntplusHrmDeviceConfig.manual_request_possible_for`. Otherwise,
        it will ensure that the DUT ignores the request.

        If the test expects a response it will also validate the content of the messages. Additionally, it makes sure
        that no messages are sent as ACK because it requests BROADCAST messages only.

        :param transmit_no: PARAMETRIZED value describing the requested times the message should be sent
        """
        page_type = pages.hrm.Hrm6CapabilitiesPage

        if page_type in self.HeartRateSensor.ant_config.manual_request_possible_for:  # pylint: disable=no-else-raise
            __response = self._do_request_for_brdcst(page_type, transmit_no)
            raise NotImplementedError('this page is not fully implemented yet')
            # TODO validate message content
        else:
            self._do_request_for_brdcst_but_expect_no_response(page_type, transmit_no)

    @balder.parametrize_by_feature(
        'transmit_no', (HeartRateSensor, 'test_criteria', 'request_transmission_numbers_for_broadcast')
    )
    def test_brdcst_page_7_battery(self, transmit_no: int):
        """
        Test that validates the correct behavior, when the controller ask for a BROADCAST message of
        :class:`Hrm7BatteryStatusPage`. The test validates that the DUT answers the correct count of requested
        messages, when the page is mentioned in :meth:`AntplusHrmDeviceConfig.manual_request_possible_for`. Otherwise,
        it will ensure that the DUT ignores the request.

        If the test expects a response it will also validate the content of the messages. Additionally, it makes sure
        that no messages are sent as ACK because it requests BROADCAST messages only.

        :param transmit_no: PARAMETRIZED value describing the requested times the message should be sent
        """
        page_type = pages.hrm.Hrm7BatteryStatusPage

        if page_type in self.HeartRateSensor.ant_config.manual_request_possible_for:
            response = self._do_request_for_brdcst(page_type, transmit_no)

            expected_bat_voltage = \
                (self.BatterySimulator.sim.discharge_characteristic.get_voltage_for(self.DO_WITH_BATTERY_LEVEL)
                 if self.HeartRateSensor.ant_config.support_battery_voltage_messuring else None)

            page_type.validate_messages(
                of_msg_collection=response,
                expected_battery_level=int(self.DO_WITH_BATTERY_LEVEL * 100),
                expected_battery_status=self.HeartRateSensor.ant_config.get_expected_battery_state_for_level(
                    int(self.DO_WITH_BATTERY_LEVEL * 100)
                ),
                expected_battery_voltage=expected_bat_voltage,
            )
        else:
            self._do_request_for_brdcst_but_expect_no_response(page_type, transmit_no)

    @balder.parametrize_by_feature(
        'transmit_no', (HeartRateSensor, 'test_criteria', 'request_transmission_numbers_for_broadcast')
    )
    def test_brdcst_page_9_device_info(self, transmit_no: int):
        """
        Test that validates the correct behavior, when the controller ask for a BROADCAST message of
        :class:`Hrm9DeviceInformationPage`. The test validates that the DUT answers the correct count of requested
        messages, when the page is mentioned in :meth:`AntplusHrmDeviceConfig.manual_request_possible_for`. Otherwise,
        it will ensure that the DUT ignores the request.

        If the test expects a response it will also validate the content of the messages. Additionally, it makes sure
        that no messages are sent as ACK because it requests BROADCAST messages only.

        :param transmit_no: PARAMETRIZED value describing the requested times the message should be sent
        """
        # check that it is not within the transmission or if data is valid (depending on setting)
        page_type = pages.hrm.Hrm9DeviceInformationPage

        if page_type in self.HeartRateSensor.ant_config.manual_request_possible_for:
            response = self._do_request_for_brdcst(page_type, transmit_no)

            page_type.validate_messages(
                of_msg_collection=response,
            )
        else:
            self._do_request_for_brdcst_but_expect_no_response(page_type, transmit_no)
