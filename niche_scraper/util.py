import locale
import math
import base64
import os.path
import shutil
import requests
import json
import selenium
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

class DriverSingleton:
    def __init__(self, 
                 login_cookie_name=CONFIG.web.LoginCookieName, 
                 login_cookie_value=CONFIG.web.LoginCookieValue):
        self.d = None
        self.login_cookie_name = login_cookie_name
        self.login_cookie_value = login_cookie_value

    @property
    def driver(self):
        if not self.d:
            self.d = selenium.webdriver.Safari()
            self.d.get('https://www.niche.com/account/')
            self.d.add_cookie(
                {'name' : self.login_cookie_name, 
                 'value' : self.login_cookie_value, 
                 'domain' : '.www.niche.com'})
        return self.d

Driver = DriverSingleton()

def get_page(url, 
             cache=CONFIG.web.Cache, 
             login_cookie_name=CONFIG.web.LoginCookieName, 
             login_cookie_value=CONFIG.web.LoginCookieValue):
    cachefilename = CONFIG.user_cache_dir.joinpath(b64string(url))
    data = None
    if cache and os.path.isfile(cachefilename):
        data = open(cachefilename, 'r').read()
    else:
        cookies = {}
        if login_cookie_name and login_cookie_value:
            cookies[login_cookie_name] = login_cookie_value
        # add check on result code, and return None on redirect.
        res = requests.get(
            url, 
            headers={'User-Agent': CONFIG.web.UserAgent}, 
            allow_redirects=False,
            cookies=cookies)
        if res.status_code in [301, 302]:
            return None
        data = res.content
        if cache:
            os.makedirs(CONFIG.user_cache_dir, exist_ok=True)
            data_conv = data.decode('utf-8')
            open(cachefilename, 'w').write(data_conv)
    return BeautifulSoup(data, 'html.parser')

def get_page(url, 
             cache=CONFIG.web.Cache, 
             login_cookie_name=CONFIG.web.LoginCookieName, 
             login_cookie_value=CONFIG.web.LoginCookieValue):
    cachefilename = CONFIG.user_cache_dir.joinpath(b64string(url))
    data = None
    if cache and os.path.isfile(cachefilename):
        data = open(cachefilename, 'r').read()
    else:
        Driver.driver.get(url)
        data = Driver.driver.page_source
        #har = json.loads(Driver.driver.get_log('har')[0]['message'])
        #status = har['log']['entries'][0]['response']['status']
        #if status in ['301', '302']:
        #    return None
        if cache:
            os.makedirs(CONFIG.user_cache_dir, exist_ok=True)
            data_conv = data.decode('utf-8')
            open(cachefilename, 'w').write(data_conv)
    return BeautifulSoup(data, 'html.parser')


def _rescale_miles(base):
    l = math.log(base+1.0)
    p = 30.0-(l*3.0)
    if p < 0: return base
    return int((base+1.0)*(1.0+(p/100.0)))

def get_miles(lat, lon):
    base = distance.distance(
        (CONFIG.geo.HomeLatitude, CONFIG.geo.HomeLongitude), 
        (lat,lon)).miles
    if CONFIG.geo.CorrectShortDistances:
        return _rescale_miles(base)
    return int(base)

def get_travel(miles):
    res = 'Fly'
    if miles < CONFIG.geo.DriveDistance:
        res = 'Drive'
    if miles < CONFIG.geo.CommuteDistance:
        res = 'Commute'
    if miles < CONFIG.geo.PublicTransDistance:
        res = 'Public Trans'
    return res

def get_size(nStudents):
    if (nStudents <= CONFIG.general.Small): return 'Small'
    if (nStudents >= CONFIG.general.Large): return 'Large'
    return 'Meduim'