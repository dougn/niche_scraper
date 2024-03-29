import click
import csv
from .core import School, rotated_rows_iter, load_schools
from .fields import *
from .util import BASE_URL, flush_cache
from .config import CONFIG
from .gdoc import Workbook

@click.command()
@click.option('--flush', is_flag=True)
@click.option('--google', is_flag=True)
@click.argument('urllist', required=False, type=click.File('r'))
@click.argument('key', default='sheet1 - Key.csv')
@click.argument('main', default='sheet2 - sortable.csv')
@click.argument('collapsed', default='sheet3 - collapsed.csv')
@click.argument('rotated', default='sheet4 - rotated.csv')
def main(flush, google, urllist, key, main, collapsed, rotated):
    """
    """
    if flush:
        flush_cache()
    if urllist is None:
        schools = load_schools(False)
        print("Writing schools.lst")
        with open('schools.lst', 'w') as lst:
            for s in schools:
                lst.write(s.urls['main']+'\n')
    else:
        urls = [url.strip() for url in urllist]
        schools = [School(url) for url in urls if url.startswith(BASE_URL)]
    if google:
        wkb = Workbook()
        wkb.write(schools)
    else:
        with open(main, 'w', newline='') as fmain:
            wmain = csv.DictWriter(fmain, fieldnames=COLUMNS)
            wmain.writerow(PREHEADERROW)
            wmain.writeheader()
            wmain.writerows(s.row for s in schools)
        with open(collapsed, 'w', newline='') as fcoll:
            wcoll = csv.DictWriter(fcoll, fieldnames=COLLAPSED, extrasaction='ignore')
            wcoll.writerow(PREHEADERROW)
            wcoll.writeheader()
            wcoll.writerows(s.row for s in schools)
        with open(rotated, 'w', newline='') as frot:
            wrota = csv.writer(frot)
            wrota.writerows(rotated_rows_iter(schools))
        write_key(key)

if __name__ == '__main__':
    main()
