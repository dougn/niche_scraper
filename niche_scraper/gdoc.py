import gspread
import oauth2client

from oauth2client.service_account import ServiceAccountCredentials

from .config import CONFIG
from .fields import *
from.core import rotated_rows_iter

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']


def _i2col(i):
    """Given an index, return the column string:

    0 = 'A'
    27 = 'AB'
    758 = 'ACE'
    """
    b = (i//26) - 1
    if b>=0:
        return _i2col(b) + chr(65+(i%26))
    return chr(65+(i%26))

class _I2COL:
    """Indexing and slicing interface for turning indexes into column names and ranges

    I2COL[4] == 'D'
    I2COL[3:6] == 'C:G'
    I2COL(758) == 'ACE'
    """
    def __getitem__(self, i):
        if isinstance(i, slice):
            return _i2col(i.start) + ':' + _i2col(i.stop)
        return _i2col(i)
    def __call__(self, i, j=None):
        if j is not None:
            return self[i:j]
        return self[i]

I2COL = _I2COL()

class Workbook:
    def __init__(self, jsonfile=CONFIG.google.CredentialsJSONFile,
                 workbook_key=CONFIG.google.WorkbookKey):
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(jsonfile, scope)
        self.gs = gspread.authorize(self.credentials)
        self.gwkb = self.gs.open_by_key(workbook_key)
        # need to add system to create the pages from scratch.
        self.sheets = {s.title: s for s in self.gwkb.worksheets()}
        self.sKey = self.sheets['Key']
        self.sSortable = self.sheets['sortable']
        self.sCollapsed = self.sheets['collapsed']
        self.sRotated = self.sheets['rotated']
    
    def write(self, schools):
        self.write_sortable(schools)
        self.write_collapsed(schools)
        self.write_rotated(schools)

    def write_sortable(self, schools):
        print("Writing sortable.")
        for I, school in enumerate(schools, 3):
            C = I2COL[len(COLUMNS)]
            row = self.sSortable.range(f'A{I}:{C}{I}')
            for n, c in zip(COLUMNS, row):
                c.value = school.row.get(n, '')
            self.sSortable.update_cells(row)

    def write_collapsed(self, schools):
        print("Writing collapsed.")
        for I, school in enumerate(schools, 3):
            C = I2COL[len(COLLAPSED)]
            row = self.sCollapsed.range(f'A{I}:{C}{I}')
            for n, c in zip(COLLAPSED, row):
                c.value = school.row.get(n, '')
            self.sCollapsed.update_cells(row)

    def write_rotated(self, schools):
        # we don't need to do the rotation... ya know...
        print("Writing rotated.")
        rows = rotated_rows_iter(schools)
        C = I2COL[len(schools)+2]
        for I, drow in enumerate(rows,1):
            row = self.sRotated.range(f'C{I}:{C}{I}')
            for c, v in zip(row, drow[2:]):
                c.value = v
            self.sCollapsed.update_cells(row)