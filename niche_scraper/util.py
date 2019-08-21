import locale
import base64
import os.path
import shutil
import requests
from bs4 import BeautifulSoup
from geopy import distance
from .config import CONFIG

BASE_URL='https://www.niche.com/colleges/'
EMDASH='—'

locale.setlocale( locale.LC_ALL, '' )

dol2int = lambda x: 0 if x.replace(EMDASH, '').replace('-','').strip() == '' else int(x.strip().replace('$','').replace(',',''), 10)
int2dol = lambda x: locale.currency(x, grouping=True)[:-3]

def b64string(string):
    return base64.b64encode(string.encode('ascii')).decode("ascii", "ignore")[:-2]

def flush_cache():
    shutil.rmtree(CONFIG.user_cache_dir, ignore_errors=True)

def get_page(url, cache=CONFIG.web.Cache):
    cachefilename = CONFIG.user_cache_dir.joinpath(b64string(url))
    data = None
    if cache and os.path.isfile(cachefilename):
        data = open(cachefilename, 'r').read()
    else:
        # add check on result code, and return None on redirect.
        res = requests.get(url, headers={'User-Agent': CONFIG.web.UserAgent}, allow_redirects=False)
        if res.status_code == 301:
            return None
        data = res.content
        if cache:
            os.makedirs(CONFIG.user_cache_dir, exist_ok=True)
            data_conv = data.decode('utf-8')
            open(cachefilename, 'w').write(data_conv)
    return BeautifulSoup(data, 'html.parser')

def get_miles(lat, lon):
    return int(distance.distance(
        (CONFIG.geo_location.HomeLatitude, CONFIG.geo_location.HomeLongitude), 
        (lat,lon)).miles)

def get_travel(miles):
    res = 'Fly'
    if miles < CONFIG.geo_location.DriveDistance:
        res = 'Drive'
    if miles < CONFIG.geo_location.CommuteDistance:
        res = 'Commute'
    if miles < CONFIG.geo_location.PublicTransDistance:
        res = 'Public Trans'
    return res
