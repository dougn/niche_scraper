import locale
import requests
from bs4 import BeautifulSoup
from geopy import distance
from .config import CONFIG

BASE_URL='https://www.niche.com/colleges/'
EMDASH='—'

locale.setlocale( locale.LC_ALL, '' )

dol2int = lambda x: 0 if x.replace(EMDASH, '').replace('-','').strip() == '' else int(x.strip().replace('$','').replace(',',''), 10)
int2dol = lambda x: locale.currency(x, grouping=True)[:-3]

def get_page(url):
    return BeautifulSoup(requests.get(
        url, headers={'User-Agent': CONFIG.web.UserAgent}).content, 'html.parser')

def get_miles(lat, lon):
    return int(distance.distance(
        (CONFIG.geo_location.HomeLatitude, CONFIG.geo_location.HomeLongitude), 
        (lat,lon)).miles)
