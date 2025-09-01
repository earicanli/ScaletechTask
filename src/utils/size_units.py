_TO_SHORT_MAP = {
    'b': 'b', 'byte': 'b', 'bytes': 'b',
    'kb': 'kb', 'kilobyte': 'kb', 'kilobytes': 'kb',
    'mb': 'mb', 'megabyte': 'mb', 'megabytes': 'mb',
    'gb': 'gb', 'gigabyte': 'gb', 'gigabytes': 'gb',
    'tb': 'tb', 'terabyte': 'tb', 'terabytes': 'tb'
}

_TO_LONG_MAP = {
    'b': 'byte', 'byte': 'byte', 'bytes': 'byte',
    'kb': 'kilobyte', 'kilobyte': 'kilobyte', 'kilobytes': 'kilobyte',
    'mb': 'megabyte', 'megabyte': 'megabyte', 'megabytes': 'megabyte',
    'gb': 'gigabyte', 'gigabyte': 'gigabyte', 'gigabytes': 'gigabyte',
    'tb': 'terabyte', 'terabyte': 'terabyte', 'terabytes': 'terabyte'
}

_CONVERSION_MAPS = {
    'short': _TO_SHORT_MAP,
    'long': _TO_LONG_MAP,
}


def coerce_sizing_unit(unit, to='short'):

    if to not in _CONVERSION_MAPS.keys():
        raise ValueError(f'Invalid "to" value: ({to})')

    try:
        res = _CONVERSION_MAPS[to][unit.lower()]
        return res
    except KeyError:
        raise ValueError(f'Invalid "unit" value: "{unit}"')