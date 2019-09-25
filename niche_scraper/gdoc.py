
def _i2col(i):
    """Given an index, return the column string:

    0 = 'A'
    27 = 'AB'
    758 = 'ACE'
    """
    b = (i//26) - 1
    if b>=0:
        return i2col(b) + chr(65+(i%26))
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

