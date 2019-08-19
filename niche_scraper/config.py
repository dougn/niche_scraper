# Copyright (c) 2019 Doug Napoleone

from .usrcfg import UserConfig, Section, StringOption, IntegerOption, FloatOption
from .version import __version__, __author__

__all__ = ['AppConfig', 'CONFIG']


class AppConfig(UserConfig):
    """User configuration for the Niche web scaper
    """

    application = "niche-scraper.config"
    author = __author__
    ## only take the first two version numbers, they denote the compatability.
    version = '.'.join(__version__.split('.')[:2])

    class GeneralSection(Section):
        """
        """
    general = GeneralSection()
    class WebSection(Section):
        """Options for the 
        """
        UserAgent = StringOption("User-Agent to use when talking to niche.com", 
            default='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')
    web = WebSection()
    class GeoLocationSection(Section):
        """GeoLocation options. Distance measurements are in miles from 
        (HomeLatitude, HomeLongitude) in a direct line (a.k.a. as the crow flies) to the school.
        Used to determine if the school can be commuted to, driven to, or a flight is required.
        How hard is it to get home if needed?
        Anything over the DriveDistance is considered to require Flight.
        """
        HomeLongitude = FloatOption(
            "Longitude of your home (can begotten from google maps.)", 
            required=True)
        HomeLatitude = FloatOption(
            "Latitude of your home (can begotten from google maps.)", 
            required=True)
        HomeState = StringOption(
            "2 letter abreviation of the state you live in to determine 'InState' tuition.",
            required=True)
        HousingDistance = IntegerOption(
            "If the school is less than this many miles away, then housing is not required, and housing costs will NOT be added to totals. Set to 0 to force on-school housing and include housing costs.", 
            default=81,
            required=False)
        PublicTransDistance = IntegerOption(
            "If school is less than this many miles from home, public transit is an option (0 to disable.)", 
            default=0,
            required=False)
        CommuteDistance = IntegerOption(
            "If the school is less than this many miles from home, then commuting is possible (0 to disable.)", 
            default=81,
            required=False)
        DriveDistance = IntegerOption(
            "If the school is less than this many miles from home, then driving to the school is preferable to flying (0 to disable.)", 
            default=350,
            required=False)

    geo_location = GeoLocationSection()

def main():
    AppConfig(cli=True)

if __name__ == '__main__':
    main()

CONFIG = AppConfig(cli=False)