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
        c = len(COLUMNS)-1
        C = I2COL[c]
        l = len(schools)
        I = l+3
        rows = self.sSortable.range(f'A3:{C}{I}')
        for i, school in enumerate(schools):
            start = i*c+i
            end = start+c
            for name, cell in zip(COLUMNS[:-1], rows[start:end]):
                cell.value = school.row.get(name, '')
            rows[end].value = i
        self.sSortable.update_cells(rows)

    def write_collapsed(self, schools):
        print("Writing collapsed.")
        c = len(COLLAPSED)-1
        C = I2COL[c]
        l = len(schools)
        I = l+3
        rows = self.sCollapsed.range(f'A3:{C}{I}')
        for i, school in enumerate(schools):
            start = i*c+i
            end = start+c
            for name, cell in zip(COLLAPSED[:-1], rows[start:end]):
                cell.value = school.row.get(name, '')
            rows[end].value = i
        self.sCollapsed.update_cells(rows)

    def write_rotated(self, schools):
        # we don't need to do the rotation... ya know...
        # but this IS much easier
        print("Writing rotated.")
        C = I2COL[len(schools)+1]
        I = sum((len(c) for c in BREAKDOWN.values()), len(BREAKDOWN))
        cells = self.sRotated.range(f'A1:{C}{I}')
        i = 0
        for row in rotated_rows_iter(schools):
            for value in row:
                cells[i].value = value
                i+=1
        self.sRotated.update_cells(cells)
