from balderhub.ant.lib.utils.page_message_collection import PageMessageCollection
from balderhub.ant.lib.utils.pages.base_received_antplus_page import BaseReceivedAntplusPage


def filter_hrm_messages_by_toggle_bit_change(
    messages: PageMessageCollection,
) -> PageMessageCollection:
    """
    Helper function to filter all messages from a given page-message collection to only return the according to the
    spec relevant messages, because the toggle bit has changed.

    :param messages: the message collection that should be filtered
    :return: a new message collection that only holds the first messages after every toggle bit change
    """
    result = PageMessageCollection()

    if len(messages) == 0:
        return result

    def get_toggle_bit(msg: BaseReceivedAntplusPage) -> bool:
        return bool(msg.raw_data[0] & 0x80)

    toggle_bit_before = not get_toggle_bit(messages[0])
    for msg in messages:
        cur_toggle_bit = get_toggle_bit(msg)
        if toggle_bit_before != cur_toggle_bit:
            result.append(msg)
            toggle_bit_before = cur_toggle_bit
    return result
