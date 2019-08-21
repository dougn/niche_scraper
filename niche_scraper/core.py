
# TODO: clean this import stuff up (breaking up a monolithic script is a pain to refactor)
from .config import CONFIG
from .util import *
from .fields import *
import json

class School:
    def __init__(self, url):
        self.urls =dict()
        self.urls['main'] = url
        self.urls['cost'] = url+ 'cost/'
        self.urls['admissions'] = url+ 'admissions/'
        self.urls['academics'] = url + 'academics/'
        self.urls['fa'] = url + 'scholarships-financial-aid/'
        self.urls['loans'] = url + 'student-loans/'
        self.row = dict(Niche = url)
        print(url)
        self.parse()
        self.compute_costs()

    def sum(self, *fields):
        return int2dol(sum(dol2int(self.row.get(f, '0')) for f in fields))
    
    def housing_needed(self):
        if self.row.get('LoC', '') == '100%': 
            return True
        if self.row.get('LoC Required', '') == 'Yes':
            return True
        return self.row.get('Miles', 0) > CONFIG.geo_location.HousingDistance

    def is_instate(self):
        return self.row.get('State', '') == CONFIG.geo_location.HomeState
    
    def compute_costs(self):
        self.row['Miles'] = get_miles(self.latitude, self.longitude)
        self.row['Travel'] = get_travel(self.row['Miles'])
        
        self.row['Avg FA $110k+'] = int2dol(dol2int(self.row['Tuition OoS'])-
                                         dol2int(self.row['$110k+ Net']))

        self.row['IS Tot'] = self.sum('Tuition IS','Housing','Meal','Supplies')
        self.row['OoS Tot'] = self.sum('Tuition OoS','Housing','Meal','Supplies')
        self.row['Com Tot'] = self.sum('Tuition IS','Meal','Supplies')

        tosum = ['Supplies']
        tt = ''
        if self.is_instate():
            tosum.append('Tuition IS')
            tt+='IS '
        else:
            tosum.append('Tuition OoS')
            tt+='OoS '
        if self.housing_needed():
            tosum.extend(['Housing', 'Meal'])
            tt+='Campus'
        else:
            tt+='Home'
        self.row['Total'] = self.sum(*tosum)
        self.row['TBasis'] = tt

    def _parse_main(self, bs):
        """
        """
        # Name/Name
        self.row['Name'] = bs.h1.contents[0]
        print(self.row['Name'])

        # lon/lat
        lon = bs.find('meta', property='place:location:longitude')
        self.row['State'] = json.loads(lon.parent()[-1].text)['address']['addressRegion']
        self.longitude = float(lon.get('content'))
        self.latitude = float(bs.find('meta', property='place:location:latitude').get('content'))

        # Urls/[Apply, Visit, School, Info]
        buttons = bs.find_all(class_="button")
        #self.row['Apply'] = buttons[1].get('href') # problem
        #self.row['Visit'] = buttons[2].get('href') # problem
        #self.row['Info'] = buttons[-3].get('href') # problem
        self.row['School'] = bs.find_all(class_="profile__website__link")[0].get('href')

        # Ranks/*
        self.row['Overall'] = bs.find(class_="overall-grade__niche-grade").text
        ranks = bs.find_all(class_="profile-grade--two")
        self.row.update({g.contents[0].text: g.contents[1].text for g in ranks})

        # Academics/[Fulltime,Parttime]
        students = bs.find(id="students").find_all(class_="scalar__value")
        self.row['Fulltime'] = students[0].contents[0].text
        self.row['Parttime'] = students[1].text

        # Academics/[S:T, Evening]
        acc = bs.find(id="academics").find_all(class_="scalar__value")
        self.row['S:T'] = acc[0].text
        self.row['Evening'] = acc[1].text
        
        # Academics/[Grad$, Grad%, Emp%]
        after = bs.find(id="after").find_all(class_="scalar__value")
        self.row['Grad$'] = after[0].contents[0].text
        self.row['Grad%'] = after[1].contents[0].text
        self.row['Emp%'] = after[2].contents[0].text
        
        # Academics/LoC
        loc = bs.find(id="campus-life")
        if loc: loc = loc.find(class_="scalar__value")
        self.row['LoC'] = loc.text if loc else EMDASH
    

    def _parse_cost(self, bs):
        """
        """
        # Aid/FA%
        net = bs.find(id="net-price")
        sv = net.find_all(class_='scalar--three')
        self.row['FA%'] = sv[-1].contents[-1].text.split('/')[0]
        self.row['Avg FA'] =  sv[-2].contents[-1].text.split('/')[0]

        # Urls/Calc
        self.row['Calc'] =  net.find(class_="profile__website__link").get('href')

        # Aid/$110k+ Net
        self.row['$110k+ Net'] = net.find_all(class_="fact__table__row__value")[-1].contents[0]

        # Cost/[Tuition *, Housing, Meal, Supplies]
        sticker = bs.find(id="sticker-price")
        buckets = sticker.find_all(class_="blank__bucket")
        self.row['Tuition IS'] = buckets[0].find(class_="scalar__value").span.text
        self.row['Tuition OoS'] = buckets[1].find(class_="scalar__value").span.text

        vals = sticker.find_all(class_="scalar--three")

        self.row['Housing'] = vals[0].contents[-1].text.split('/')[0]
        self.row['Meal'] = vals[1].contents[-1].text.split('/')[0]
        self.row['Supplies'] = vals[2].contents[-1].text.split('/')[0]

        # Aid/[No Increase, Installments, PrePay]
        self.row['No Increase'] = vals[3].contents[-1].text
        self.row['Installments'] = vals[4].contents[-1].text
        self.row['PrePay'] = vals[5].contents[-1].text

    def _parse_fa(self, bs):
        """
        """
        self.row['Aid'] = bs.find(class_='profile__website__link').get('href')

        bd = bs.find(id='financial-aid-breakdown').find_all(class_='fact__table__row__value')
        self.row['Fed%'] = bd[0].text
        self.row['Fed$'] = bd[4].text
        self.row['State%'] = bd[1].text
        self.row['State$'] = bd[5].text
        self.row['Inst%'] = bd[2].text
        self.row['Inst$'] = bd[6].text
        self.row['Pel%'] = bd[3].text
        self.row['Pel$'] = bd[7].text
        
    def _parse_loans(self, bs):
        """
        """
        loans = bs.find(class_='blank__bucket')
        try:
            self.row['Loan$'] = loans.contents[1].find(class_='scalar__value').span.text
        except:
            self.row['Loan$'] = EMDASH
        vals = loans.find_all(class_='scalar--three')
        self.row['Loan%'] = vals[0].contents[-1].text
        self.row['Default%'] = vals[1].contents[1].span.text


    def _parse_academics(self, bs):
        """
        """
        # Academics/[Fulltime%, Parttime%, Calendar]
        vals = bs.find_all(class_="scalar--three")
        self.row['Fulltime%'] = vals[0].contents[-1].text
        self.row['Parttime%'] = vals[1].contents[-1].text
        self.row['Calendar'] = vals[2].contents[-1].text


    def _parse_admissions(self, bs):
        """
        """
        stats = bs.find(id="admissions-statistics")
        if not stats:
            self.row['Acceptance Rate'] = '100%'
            return
        buckets = stats.find_all(class_="blank__bucket")
        self.row['Acceptance Rate'] = buckets[0].contents[-1].contents[-1].text
        self.row['SAT'] = buckets[2].contents[0].contents[-1].text
        self.row['ACT'] = buckets[3].contents[0].contents[-1].text

        vals = stats.find_all(class_="scalar--three")
        self.row['Early Rate'] = vals[0].contents[-1].text
        self.row['Applicants'] = vals[1].contents[-1].text
        self.row['SAT Reading'] = vals[2].contents[-1].text
        self.row['SAT Math'] = vals[3].contents[-1].text
        self.row['SAT%'] = vals[4].contents[-1].text
        self.row['ACT English'] = vals[5].contents[-1].text
        self.row['ACT Math'] = vals[6].contents[-1].text
        self.row['ACT Writing'] = vals[7].contents[-1].text
        self.row['ACT%'] = vals[8].contents[-1].text

        dead = bs.find(id="admissions-deadlines")
        buckets = dead.find_all(class_="blank__bucket")
        self.row['Deadline'] = buckets[0].contents[0].contents[-1].text
        self.row['Fee'] = buckets[1].contents[0].contents[-1].text

        vals = dead.find_all(class_="scalar--three")
        self.row['Decision Deadline'] = vals[0].contents[-1].text
        self.row['Action Deadline'] = vals[1].contents[-1].text

        self.row['Early Decision'] = vals[2].contents[-1].text
        self.row['Early Action'] = vals[3].contents[-1].text
        self.row['Common App'] = vals[4].contents[-1].text
        self.row['Coalition App'] = vals[5].contents[-1].text

        try:
            self.row['Apply'] = dead.find(class_='profile__website__link').get('href')
        except:
            pass

        vals = bs.find(id="admissions-requirements").find_all(class_="fact__table__row__value")
        self.row['HS GPA'] = vals[0].text
        self.row['HS Rank'] = vals[1].text
        self.row['HS Transcript'] = vals[2].text
        self.row['Col Prep Courses'] = vals[3].text
        self.row['SAT/ACT'] = vals[4].text
        self.row['Recomendations'] = vals[5].text

    def parse(self):
        """
        Parse all the pages into the primary row data.
        """
        for page, url in self.urls.items():
            bs = get_page(url)
            if bs is not None:
                getattr(self, '_parse_'+page)(bs)
        

def rotated_rows_iter(schools):
    prefix=['', '']
    cathead = [''] *(len(schools)+1)
    def rotated_row(name):
        row = [s.row.get(name, '') for s in schools]
        row[0:0] = prefix
        return row
    for cat, vals in BREAKDOWN.items():
        yield [cat,] + cathead
        for name in vals:
            prefix[1] = name
            yield rotated_row(name)
