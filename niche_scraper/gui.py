import gooey
import argparse
from .config import *

@gooey.Gooey(
        advanced=True,
        show_config=True,
        program_name='niche_scraper',
        #navigation='TABBED',
        tabbed_groups=True,
)
def main():
    #parser = gooey.GooeyParser()
    parser = argparse.ArgumentParser('')
    #sub_parsers = parser.add_subparsers(title="subTitle", description="SubDescription", help="SubHElp")
    #mainparser = sub_parsers.add_parser('Generate')
    #mainparser.add_argument('foo')
    #cfgparser = sub_parsers.add_parser('Config')
    cfg = AppConfig(cli=False, parser=parser)
    args = parser.parse_args()

if __name__ == '__main__':
    main()

