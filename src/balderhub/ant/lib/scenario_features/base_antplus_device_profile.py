from collections import OrderedDict

import balder

from balderhub.ant.lib.utils import pages


class BaseAntplusDeviceProfile(balder.Feature):
    """
    Base class for an ANT+ Device Profile
    """

    ALL_PAGES = None

    @classmethod
    def get_existing_pages_for_profile(cls) -> OrderedDict[int, pages.BaseAntplusPage]:
        """
        :return: returns an ordered dictionary mapping with the Page-ID and the Page this profile supports
        """

        if cls.ALL_PAGES is None:
            raise ValueError(f'you need to define ALL_PAGES within your profile {cls.__name__}')

        result = []
        for page in sorted(cls.ALL_PAGES, key=lambda x: x.PAGE_ID):
            if page.PAGE_ID is None:
                raise ValueError('you need to define a PAGE_ID as soon as the page is used within a profile')
            result.append((page.PAGE_ID, page))
        return OrderedDict(result)
