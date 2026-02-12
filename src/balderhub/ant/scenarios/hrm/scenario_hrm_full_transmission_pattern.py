import logging
import math
import time

import balder
from balder.connections import DCPowerConnection

from balderhub.ant.lib.utils import pages
import balderhub.battery.lib.scenario_features
from balderhub.heart.lib.scenario_features import HeartBeatFeature, StrapDockingFeature

from .base_hrm_scenario import BaseHrmScenario
from ...lib.utils.support import filter_hrm_messages_by_toggle_bit_change

logger = logging.getLogger(__name__)


# TODO split up this scenario into single components to make sure that subset of tests can run even without test hw
class ScenarioHrmDeviceProfileFullTransmissionPattern(BaseHrmScenario):
    """Test scenario that observes a full ANT transmission pattern time frame and then validates requirements defined
    in the HRM device profile"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.transmission_pattern_sequence_count < 2:
            raise ValueError('the sequence need to be at least 2 times - some test rely on that')

    COUNT_OF_MAX_POSSIBLE_BACKGROUND_PAGES = 6

    DO_SEQUENCE_WITH_HEART_RATE = 60

    DO_WITH_BATTERY_LEVEL = 1.0

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
        # _is_cnn = IsConnected()  # TODO
        strap = StrapDockingFeature()

    @balder.connect(HeartRateSensor, over_connection=balder.Connection)  # pylint: disable=undefined-variable
    class HeartRateHost(BaseHrmScenario.HeartRateHost):
        """device receiving the heart rate data"""

    @property
    def transmission_pattern_duration_sec(self):
        """expected seconds to receive a full transmission pattern"""
        # TODO maybe also considering overflow test of heart beat?
        # TODO maybe also considering overflow of Heart Beat Event Time? - just use max time of all
        return (64 + 4) * self.COUNT_OF_MAX_POSSIBLE_BACKGROUND_PAGES * 8070/32768

    @property
    def transmission_pattern_sequence_count(self):
        """amount of transmission pattern sequences that should be waited for receiving the initial data"""
        return 2

    @property
    def total_observing_time(self):
        """
        :return: returns the total observing time calculated based on
                 :meth:`ScenarioHrmDeviceProfileFullTransmissionPattern.transmission_pattern_duration_sec` multiplied
                 with :meth:`ScenarioHrmDeviceProfileFullTransmissionPattern.transmission_pattern_sequence_count`
        """
        total_time =  self.transmission_pattern_duration_sec * self.transmission_pattern_sequence_count
        total_time += 2 # wait a little bit longer
        return total_time

    @property
    def min_expected_heart_beats(self):
        """
        :return: returns the minimum expected heart beats according to the observation time given in
                 :meth:`ScenarioHrmDeviceProfileFullTransmissionPattern.total_observing_time` divided by heart beat
                 frequency
        """
        return math.floor(self.total_observing_time / (self.DO_SEQUENCE_WITH_HEART_RATE / 60) )

    @balder.fixture('variation')
    def heart_beat_established(self):
        """make sure that heart beat is established, before entering the variation"""
        yield from self.Heart.heart.fixt_make_sure_heart_beat_established(with_bpm=60, restore_entry_state=True)

    @balder.fixture('variation')
    def chest_strap_attached(self, heart_beat_established):  # pylint: disable=unused-argument
        """make sure that chest strap is attached, before entering the variation"""
        yield from self.HeartRateSensor.strap.fixt_make_sure_to_be_attached(restore_entry_state=True)

    @balder.fixture('variation')
    def device_powered_on(self, heart_beat_established, chest_strap_attached):  # pylint: disable=unused-argument
        """make sure that device is powered on, before entering the variation"""
        yield from self.BatterySimulator.sim.fixt_make_sure_device_is_powered_on(
            with_level=self.DO_WITH_BATTERY_LEVEL,
            restore_entry_state=True
        )

    @balder.fixture('variation')
    def ant_is_disconnected(self, device_powered_on):  # pylint: disable=unused-argument
        """make sure that ANT is disconnected, before entering the variation"""
        yield from self.HeartRateHost.controller.fixt_make_sure_ant_channel_is_closed()

    @balder.fixture('variation')
    def run_transmission_pattern_session(self, ant_is_disconnected):  # pylint: disable=unused-argument
        """
        fixture that runs the recoding session - during this fixture the normal transmission pattern is recorded,
        which will be analyzed by the tests within this scenario
        """
        logger.info(f'set heart beat to {self.DO_SEQUENCE_WITH_HEART_RATE}')
        self.Heart.heart.start(self.DO_SEQUENCE_WITH_HEART_RATE)

        logger.info('connect with ANT device')
        self.HeartRateHost.controller.open_channel()

        time_to_wait = self.total_observing_time

        logger.info(f'now wait for {time_to_wait:.2f} seconds to make sure that we receive '
                    f'{self.transmission_pattern_sequence_count} full transmission patterns')
        time.sleep(time_to_wait)
        logger.info('close ANT device channel')
        self.HeartRateHost.controller.close_channel()

        logger.info('stop heart beat')
        self.Heart.heart.stop()

    def test_general_profile_consistency(self):
        """
        This test executed the profile validation method
        :meth:`AntplusControllerHrmFeature.validate_profile_consistency` that validates all general valid conditions of
        the profile.
        """
        validation_report = self.HeartRateHost.controller.get_profile_consistency_validation_report()
        for cur_descr, cur_result in validation_report.items():
            if cur_result is None:
                logger.info(f"VALIDATION SUCCESSFULLY: {cur_descr}")
            else:
                logger.error(f"VALIDATION FAILED:      {cur_descr}: {cur_result}")
        errors_only = [(k, v) for k, v in validation_report.items() if v is not None]
        assert len(errors_only) == 0, ("detect errors within the profile: \n" +
                                       '\n'.join([f"- {k}: ERROR MESSAGE `{v}`" for k, v in errors_only]) + '\n')

    def test_validate_heart_beat_counts(self):
        """
        This test reads all messages and makes sure that there is no beat loss.
        """
        messages = self.HeartRateHost.controller.received_broadcast_messages

        last_beat_count = messages[0].heart_beat_count
        for idx, cur_msg in enumerate(messages):

            if last_beat_count == cur_msg.heart_beat_count:
                continue

            normalized_cur_beat_count = \
                cur_msg.heart_beat_count \
                    if last_beat_count < cur_msg.heart_beat_count \
                    else (cur_msg.heart_beat_count + 0x100)

            assert normalized_cur_beat_count == last_beat_count + 1, \
                (f"received unexpected beat count {cur_msg.heart_beat_count} (beat before was {last_beat_count}) "
                 f"in message {cur_msg} at index {idx}")

            last_beat_count = cur_msg.heart_beat_count

    def test_validate_heart_beat_event_time(self):
        """
        This test reads the beat time of all events and check that these values have a exact diff-time of the set heart
        rate.
        """

        messages = self.HeartRateHost.controller.received_broadcast_messages

        assert len(messages) > 0, "did not receive any messages"

        expected_diff_time_sec =  60 / self.DO_SEQUENCE_WITH_HEART_RATE
        allowed_min_diff_time_sec, allowed_max_diff_time_sec = \
            self.HeartRateSensor.test_criteria.get_allowed_min_max_rr_value_for(expected_diff_time_sec)
        allowed_min_diff_time = int(allowed_min_diff_time_sec * 1024)
        allowed_max_diff_time = int(allowed_max_diff_time_sec * 1024)

        logger.info('calculate normalized heat beat event time')
        skipped_beat_counts = 0
        last_beat_msg_idx = 0
        for idx, cur_message in enumerate(messages):
            last_beat_msg = messages[last_beat_msg_idx]
            # handle overflow if necessary
            cur_message_beat_count = cur_message.heart_beat_count \
                if cur_message.heart_beat_count > last_beat_msg.heart_beat_count \
                else (cur_message.heart_beat_count + 0x100)

            if last_beat_msg.heart_beat_count == cur_message.heart_beat_count:
                # same beat -> make sure that time is still the same
                assert last_beat_msg.heart_beat_event_time == cur_message.heart_beat_event_time
                continue

            # beat is different

            if skipped_beat_counts < self.HeartRateSensor.test_criteria.first_number_of_beats_to_skip:
                logger.debug(f'skip check between beat {last_beat_msg.heart_beat_count} (idx={last_beat_msg_idx}) '
                             f'and {cur_message.heart_beat_count} (idx={idx}) because test is configured to skip the '
                             f'first {self.HeartRateSensor.test_criteria.first_number_of_beats_to_skip} beats')
                skipped_beat_counts += 1
            else:
                # -> check that it is exactly one higher
                assert cur_message_beat_count == last_beat_msg.heart_beat_count + 1, \
                    (f"unexpected beat count {cur_message.heart_beat_count} of msg at idx {idx} "
                     f"(beat count before was {last_beat_msg.heart_beat_count}) )")

                cur_message_event_time = (cur_message.heart_beat_event_time + 0x10000) \
                    if cur_message.heart_beat_event_time < last_beat_msg.heart_beat_event_time \
                    else cur_message.heart_beat_event_time

                cur_message_diff_time = cur_message_event_time - last_beat_msg.heart_beat_event_time

                assert allowed_min_diff_time <= cur_message_diff_time <= allowed_max_diff_time, \
                    (f"difference detected between heart beat {last_beat_msg.heart_beat_count} "
                     f"(idx: {last_beat_msg_idx}) and heart beat {cur_message.heart_beat_count} (idx: {idx}): "
                     f"received: {cur_message_diff_time} (expected value between {allowed_min_diff_time} and "
                     f"{allowed_max_diff_time} for configured {self.DO_SEQUENCE_WITH_HEART_RATE} BPM)")
            last_beat_msg_idx = idx

    def test_main_page_0_default(self):
        """
        This test validates the content of the main page 0, if it is expected that this page is the main page.
        """
        page_type = pages.hrm.Hrm0DefaultDataPage

        if self.HeartRateSensor.ant_config.expected_main_page == page_type:
            logger.info(f'make sure page 0 is the active main page '
                        f'(expected behavior according `{self.HeartRateSensor.ant_config.__class__}`)')
            existing_main_pages = self.HeartRateHost.controller.determine_main_pages()
            assert page_type in existing_main_pages, \
                (f"did not find expected main page `{page_type}` within determined MAIN "
                 f"pages {existing_main_pages}")
            # nothing more to test, because data is empty
            all_msgs = self.HeartRateHost.controller.received_broadcast_messages
            msgs_of_interest = all_msgs.filter_by_type(page_type=page_type)

            for cur_msg in msgs_of_interest:
                msg_idx = all_msgs.index(cur_msg)
                assert cur_msg.raw_data[1] == 0xFF, \
                    f"reserved byte 1 is not 0xFF, is {hex(cur_msg.raw_data[1])} for message at index {msg_idx}"
                assert cur_msg.raw_data[2] == 0xFF, \
                    f"reserved byte 2 is not 0xFF, is {hex(cur_msg.raw_data[2])} for message at index {msg_idx}"
                assert cur_msg.raw_data[3] == 0xFF, \
                    f"reserved byte 2 is not 0xFF, is {hex(cur_msg.raw_data[3])} for message at index {msg_idx}"
        else:
            logger.info(f'make sure page 0 is NOT an active main page '
                        f'(expected behavior according `{self.HeartRateSensor.ant_config.__class__}`)')
            existing_main_pages = self.HeartRateHost.controller.determine_main_pages()
            existing_background_pages = self.HeartRateHost.controller.determine_background_pages()

            assert page_type not in existing_main_pages, \
                (f"found not-expected main page `{page_type}` within determined MAIN "
                 f"pages {existing_main_pages}")
            assert page_type not in existing_background_pages, \
                (f"found not-expected main page `{page_type}` within determined MAIN "
                 f"pages {existing_background_pages}")

    def test_background_page_1_operating_time(self):
        """
        This test validates the content of the background page 1, which was sent during the session, if it was
        expected, that this page is an active background page.
        """
        page_type = pages.hrm.Hrm1CumulativeOperationTimePage

        if page_type in self.HeartRateSensor.ant_config.expected_background_pages:
            logger.info(f'make sure page 1 is a background page '
                        f'(expected behavior according `{self.HeartRateSensor.ant_config.__class__}`)')
            existing_background_pages = self.HeartRateHost.controller.determine_background_pages()
            assert page_type in existing_background_pages, \
                (f"did not find expected background page `{page_type}` within determined BACKGROUND "
                 f"pages {existing_background_pages}")

            # todo check that we have received at least two cycles (necessary - check in __init__()!)
            page_type.validate_messages(
                of_msg_collection=self.HeartRateHost.controller.received_broadcast_messages,
            )
        else:
            logger.info(f'make sure page 1 is not a background page '
                        f'(expected behavior according `{self.HeartRateSensor.ant_config.__class__}`)')
            existing_main_pages = self.HeartRateHost.controller.determine_main_pages()
            existing_background_pages = self.HeartRateHost.controller.determine_background_pages()

            assert page_type not in existing_main_pages, \
                (f"found not-expected main page `{page_type}` within determined MAIN "
                 f"pages {existing_background_pages}")
            assert page_type not in existing_background_pages, \
                (f"found not-expected main page `{page_type}` within determined BACKGROUND "
                 f"pages {existing_background_pages}")

    def test_background_page_2_manufacturer(self):
        """
        This test validates the content of the background page 2, which was sent during the session, if it was
        expected, that this page is an active background page.
        """
        page_type = pages.hrm.Hrm2ManufacturerInformationPage

        existing_background_pages = self.HeartRateHost.controller.determine_background_pages()
        assert page_type in existing_background_pages, \
            f"page type {page_type} not found in background page list: `{existing_background_pages}`"

        # TODO maybe use coherent messages only
        msg = filter_hrm_messages_by_toggle_bit_change(
            self.HeartRateHost.controller.received_broadcast_messages
        ).filter_by_type(page_type=page_type)

        assert len(msg) >= self.transmission_pattern_sequence_count, \
            (f"expect more than {self.transmission_pattern_sequence_count} messages of type {page_type}, "
             f"because the transmission pattern sequence count if {self.transmission_pattern_sequence_count}, "
             f"but just detect {len(msg)} independent messages")

        self.HeartRateHost.controller.validate_page_2_manufacturer()

    def test_background_page_3_product(self):
        """
        This test validates the content of the background page 3, which was sent during the session, if it was
        expected, that this page is an active background page.
        """
        page_type = pages.hrm.Hrm3ProductInformationPage

        existing_background_pages = self.HeartRateHost.controller.determine_background_pages()
        assert page_type in existing_background_pages, \
            f"page type {page_type} not found in background page list: `{existing_background_pages}`"

        # TODO maybe use coherent messages only
        msg = filter_hrm_messages_by_toggle_bit_change(
            self.HeartRateHost.controller.received_broadcast_messages
        ).filter_by_type(page_type=page_type)

        assert len(msg) >= self.transmission_pattern_sequence_count, \
            (f"expect more than {self.transmission_pattern_sequence_count} messages of type {page_type}, "
             f"because the transmission pattern sequence count if {self.transmission_pattern_sequence_count}, "
             f"but just detect {len(msg)} independent messages")

        self.HeartRateHost.controller.validate_page_3_product()

    def test_main_page_4_previous_beat(self):
        """
        This test validates the content of the main page 4, if it is expected that this page is the main page.
        """
        page_type = pages.hrm.Hrm4PreviousHeartBeatEventTimePage

        if self.HeartRateSensor.ant_config.expected_main_page == page_type:
            logger.info('make sure that page 4 is a normal main page')
            existing_main_pages = self.HeartRateHost.controller.determine_main_pages()
            assert page_type in existing_main_pages, \
                (f"did not find expected main page `{page_type}` within determined MAIN "
                 f"pages {existing_main_pages}")
            # nothing more to test, because data is empty
            logger.info('validate that all previous heart-beat-event times are valid')

            all_msgs = self.HeartRateHost.controller.received_broadcast_messages
            msgs_of_interest = filter_hrm_messages_by_toggle_bit_change(all_msgs).filter_by_type(page_type=page_type)

            def get_last_different_heart_beat_event_time(for_idx):
                cur_event_time = all_msgs[for_idx].heart_beat_event_time
                for inner_idx in reversed(range(0, for_idx)):
                    if all_msgs[inner_idx].heart_beat_event_time != cur_event_time:
                        return all_msgs[inner_idx].heart_beat_event_time
                raise ValueError('no other value found')

            non_first_beat_msgs = [msg for msg in all_msgs if msg.heart_beat_count != all_msgs[0].heart_beat_count]
            assert len(non_first_beat_msgs) > 0, "did not found messages with a heart beat"
            first_beat_idx = all_msgs.index(non_first_beat_msgs[0])
            for idx, msg in enumerate(all_msgs):
                # iterating over all messages, because the current event time is always valid, but
                # validating the previous-heart-beat-event-time only when toggle-bit changed (and instance of this type)
                if msg in msgs_of_interest and idx >= first_beat_idx:
                    last_heart_beat_event_time = get_last_different_heart_beat_event_time(idx)
                    assert last_heart_beat_event_time == msg.previous_heart_beat_event_time_raw, \
                        (f"received invalid previous-heart-beat-event-time "
                         f"{msg.previous_heart_beat_event_time_raw} at index {idx} "
                         f"(but last transmitted event time was {last_heart_beat_event_time})")

            logger.info(f'validated {len(msgs_of_interest)} messages -> all of them are valid')

        else:
            logger.info('make sure page 4 is a normal main page (and with that also no background page)')
            existing_main_pages = self.HeartRateHost.controller.determine_main_pages()
            existing_background_pages = self.HeartRateHost.controller.determine_background_pages()

            assert page_type not in existing_main_pages, \
                (f"found not-expected main page `{page_type}` within determined MAIN "
                 f"pages {existing_main_pages}")
            assert page_type not in existing_background_pages, \
                (f"found not-expected main page `{page_type}` within determined MAIN "
                 f"pages {existing_background_pages}")

    # TODO
    #def test_main_page_5_swim_interval_summary(self):
    #    raise NotImplementedError

    def test_background_page_6_capabilities(self):
        """
        This test validates the content of the background page 6, which was sent during the session, if it was
        expected, that this page is an active background page.
        """
        # TODO reqirement of that in background page was optional before spec 2.5
        page_type = pages.hrm.Hrm6CapabilitiesPage

        supported_spec_version = self.HeartRateSensor.ant_config.supported_spec_version
        if supported_spec_version == self.HeartRateSensor.ant_config.SupportedSpecVersion.V2_5:
            assert page_type in self.HeartRateSensor.ant_config.expected_background_pages, \
                (f"your configuration violates the spec: {page_type} needs to be a background page - "
                 f"please adjust your `AntplusHrmDeviceConfig.expected_background_pages` setting")

        existing_background_pages = self.HeartRateHost.controller.determine_background_pages()
        if page_type in self.HeartRateSensor.ant_config.expected_background_pages:

            assert page_type in existing_background_pages, \
                f"page type {page_type} not found in background page list: `{existing_background_pages}`"

            all_msgs = self.HeartRateHost.controller.received_broadcast_messages
            msgs_of_interest = all_msgs.filter_by_type(page_type=page_type)
            for msg in msgs_of_interest:
                msg_idx = all_msgs.index(msg)
                assert msg.raw_data[1] == 0xFF, \
                    f"reserved byte 1 is not 0xFF, is {hex(msg.raw_data[2])} for message at index {msg_idx}"
                assert msg.raw_data[2] & ((1 << 4) | (1 << 5)) == 0x00, \
                    (f"reserved bits 4 and 5 of byte 2 are not 0, byte has value {hex(msg.raw_data[2])} for message "
                     f"at index {msg_idx}")
                assert msg.raw_data[3] & ((1 << 4) | (1 << 5)) == 0x00, \
                    (f"reserved bits 4 and 5 of byte 3 are not 0, byte has value {hex(msg.raw_data[3])} for message "
                     f"at index {msg_idx}")
                active_bits = msg.raw_data[2]
                assert (msg.raw_data[3] & ~active_bits) == 0x00, \
                    (f"some bits are active in ENABLED (byte 3: {hex(msg.raw_data[3])}) "
                     f"but 0 in SUPPORTED (byte 2: {hex(msg.raw_data[2])}) for message at index {msg_idx}")
        else:
            assert page_type not in existing_background_pages, \
                f"page type {page_type} unexpectedly found in background page list: `{existing_background_pages}`"

    def test_background_page_7_battery(self):
        """
        This test validates the content of the background page 7, which was sent during the session, if it was
        expected, that this page is an active background page.
        """
        page_type = pages.hrm.Hrm7BatteryStatusPage

        if page_type in self.HeartRateSensor.ant_config.expected_background_pages:
            logger.info(f'make sure page 7 is a background page (expected behavior according '
                        f'`{self.HeartRateSensor.ant_config.__class__}`)')
            existing_background_pages = self.HeartRateHost.controller.determine_background_pages()
            assert page_type in existing_background_pages, \
                (f"did not find expected background page `{page_type}` within determined BACKGROUND "
                 f"pages {existing_background_pages}")
            # nothing more to test, because data is empty
            all_msgs = self.HeartRateHost.controller.received_broadcast_messages

            expected_bat_voltage = \
                self.BatterySimulator.sim.discharge_characteristic.get_voltage_for(self.DO_WITH_BATTERY_LEVEL) \
                    if self.HeartRateSensor.ant_config.support_battery_voltage_messuring else None

            page_type.validate_messages(
                of_msg_collection=all_msgs,
                expected_battery_level=int(self.DO_WITH_BATTERY_LEVEL * 100),
                expected_battery_status=self.HeartRateSensor.ant_config.get_expected_battery_state_for_level(
                    int(self.DO_WITH_BATTERY_LEVEL * 100)
                ),
                expected_battery_voltage=expected_bat_voltage,
            )

        else:
            logger.info(f'make sure page 7 is not a background page '
                        f'(expected behavior according `{self.HeartRateSensor.ant_config.__class__}`)')
            existing_main_pages = self.HeartRateHost.controller.determine_main_pages()
            existing_background_pages = self.HeartRateHost.controller.determine_background_pages()

            assert page_type not in existing_main_pages, \
                (f"found not-expected main page `{page_type}` within determined MAIN "
                 f"pages {existing_background_pages}")
            assert page_type not in existing_background_pages, \
                (f"found not-expected backend page `{page_type}` within determined BACKGROUND "
                 f"pages {existing_background_pages}")

    def test_background_page_9_device_info(self):
        """
        This test validates the content of the background page 9, which was sent during the session, if it was
        expected, that this page is an active background page.
        """
        # check that it is not within the transmission or if data is valid (depending on setting)
        page_type = pages.hrm.Hrm9DeviceInformationPage

        if page_type in self.HeartRateSensor.ant_config.expected_background_pages:
            logger.info(f'make sure page 9 is a background page '
                        f'(expected behavior according `{self.HeartRateSensor.ant_config.__class__}`)')
            existing_background_pages = self.HeartRateHost.controller.determine_background_pages()
            assert page_type in existing_background_pages, \
                (f"did not find expected background page `{page_type}` within determined BACKGROUND "
                 f"pages {existing_background_pages}")
            # nothing more to test, because data is empty
            page_type.validate_messages(
                of_msg_collection=self.HeartRateHost.controller.received_broadcast_messages,
            )
        else:
            logger.info(f'make sure page 9 is not a background page '
                        f'(expected behavior according `{self.HeartRateSensor.ant_config.__class__}`)')
            existing_main_pages = self.HeartRateHost.controller.determine_main_pages()
            existing_background_pages = self.HeartRateHost.controller.determine_background_pages()

            assert page_type not in existing_main_pages, \
                (f"found not-expected main page `{page_type}` within determined MAIN "
                 f"pages {existing_background_pages}")
            assert page_type not in existing_background_pages, \
                (f"found not-expected background page `{page_type}` within determined BACKGROUND "
                 f"pages {existing_background_pages}")

    def test_no_other_background_pages_exists(self):
        """test that validates that every expected background page is within the recorded pages"""
        for existing_background_page in self.HeartRateHost.controller.determine_background_pages():
            assert existing_background_page in self.HeartRateSensor.ant_config.expected_background_pages, \
                (f"detect a background page `{existing_background_page}` in data that is not existing in the "
                 f"expected background pages: {self.HeartRateSensor.ant_config.expected_background_pages}")

    def test_no_other_main_pages_exists(self):
        """test that validates that no other main pages, then the expected one, are within the recorded pages"""

        existing_main_pages = self.HeartRateHost.controller.determine_main_pages()
        assert len(existing_main_pages) == 1, f"detect more than one main pages `{existing_main_pages}`"
        assert existing_main_pages[0] == self.HeartRateSensor.ant_config.expected_main_page, \
                (f"detect a unexpected main page `{existing_main_pages[0]}` in data that is not the expected one "
                 f"`{self.HeartRateSensor.ant_config.expected_main_page}`")
