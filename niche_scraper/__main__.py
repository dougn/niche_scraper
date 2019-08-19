import click
import csv
from .core import School, rotated_rows_iter
from .fields import *
from .util import BASE_URL

@click.command()
@click.argument('urllist', default='schools.lst', type=click.File('r'))
@click.argument('key', default='sheet1 - Key.csv')
@click.argument('main', default='sheet2 - sortable.csv')
@click.argument('collapsed', default='sheet3 - collapsed.csv')
@click.argument('rotated', default='sheet4 - rotated.csv')
def main(urllist, key, main, collapsed, rotated):
    """
    """
    urls = [url.strip() for url in urllist]
    schools = [School(url) for url in urls if url.startswith(BASE_URL)]
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
