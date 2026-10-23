"""Music theory for scores: roman numerals and chord symbols to notes, so a score writes harmony, not arithmetic.

    from theory import roman, stack, above, transpose
    roman('I V vi IV', 'D')          # ['D', 'A', 'Bm', 'G']
    roman('i bVI bIII bVII', 'd')    # ['Dm', 'Bb', 'F', 'C']: in a minor key, numerals are read over the major scale
    stack('Bm', 'g3')                # [59, 62, 66] = b3 d4 f#4: root position, from the first root at or above g3
    above('Bm', 'c2')                # 47 = b2: the root at or above c2; above('Bm', 'c2', 2) the fifth (f#2)
    transpose('Bm', 2)               # 'C#m'
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio import midi  # noqa: E402

SHARPS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLATS = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
PC = {**{n: i for i, n in enumerate(SHARPS)}, **{n: i for i, n in enumerate(FLATS)}}
MAJOR = [0, 2, 4, 5, 7, 9, 11]
QUALITY = {'': (0, 4, 7), 'm': (0, 3, 7), 'dim': (0, 3, 6), 'aug': (0, 4, 8), '5': (0, 7), 'sus2': (0, 2, 7),
           'sus4': (0, 5, 7), '6': (0, 4, 7, 9), 'm6': (0, 3, 7, 9), '7': (0, 4, 7, 10), 'maj7': (0, 4, 7, 11),
           'm7': (0, 3, 7, 10), 'm7b5': (0, 3, 6, 10), 'dim7': (0, 3, 6, 9), 'add9': (0, 4, 7, 14),
           'madd9': (0, 3, 7, 14), '9': (0, 4, 7, 10, 14), 'maj9': (0, 4, 7, 11, 14), 'm9': (0, 3, 7, 10, 14)}
ROMAN = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii']
FLAT_KEYS = {('F', 0), ('Bb', 0), ('Eb', 0), ('Ab', 0), ('Db', 0), ('Gb', 0),
             ('D', 1), ('G', 1), ('C', 1), ('F', 1), ('Bb', 1), ('Eb', 1)}


def parse(symbol):
    """'Bbm7' -> (root pitch class, intervals above the root). A slash bass ('G/B') is ignored."""
    m = re.fullmatch(r'([A-G][#b]?)(.*?)(?:/[A-G][#b]?)?', symbol)
    assert m and m[2] in QUALITY, f'unknown chord {symbol!r}; qualities: {", ".join(QUALITY)}'
    return PC[m[1]], QUALITY[m[2]]


def _first(pc, lo):
    return next(m for m in range(midi(lo), midi(lo) + 12) if m % 12 == pc % 12)


def above(symbol, lo, tone=0):
    """A chord tone (0 root, 1 third, 2 fifth, 3 seventh or sixth...) at or above lo."""
    root, iv = parse(symbol)
    return _first(root + iv[tone], lo)


def stack(symbol, lo):
    """The chord in root position, from its first root at or above lo."""
    root, iv = parse(symbol)
    first = _first(root, lo)
    return [first + i for i in iv]


def transpose(symbol, k, flats=None):
    root, iv = parse(symbol)
    m = re.fullmatch(r'([A-G][#b]?)(.*?)(/[A-G][#b]?)?', symbol)
    names = FLATS if (flats if flats is not None else 'b' in m[1]) else SHARPS
    return names[(root + k) % 12] + m[2]


def roman(numerals, key):
    """Roman numerals to chord symbols. key: 'D' major, 'd' or 'Dm' minor. Upper case is major, lower case minor;
    b or # moves the degree a semitone; suffixes: 7 (dominant on upper case, minor 7th on lower), maj7, sus2, sus4,
    add9, 9, 6, dim or °, ø (half-diminished), +."""
    k = re.fullmatch(r'([A-Ga-g][#b]?)\s*(m|min|minor|maj|major)?', key.strip())
    assert k, f'unknown key {key!r}'
    minor = k[1][0].islower() or k[2] in ('m', 'min', 'minor')
    tonic_name = k[1][0].upper() + k[1][1:]
    tonic = PC[tonic_name]
    out = []
    for token in numerals.split():
        t = re.fullmatch(r'([b#]?)(VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i)(.*)', token)
        assert t, f'unknown numeral {token!r}'
        acc, num, suffix = t.groups()
        upper = num.isupper()
        root = tonic + MAJOR[ROMAN.index(num.lower())] + {'b': -1, '#': 1, '': 0}[acc]
        quality = {'': '' if upper else 'm', '7': '7' if upper else 'm7', '°': 'dim', 'dim': 'dim', 'ø': 'm7b5',
                   '+': 'aug'}.get(suffix, suffix if upper else 'm' + suffix)
        flats = acc == 'b' or (tonic_name, int(minor)) in FLAT_KEYS
        out.append((FLATS if flats else SHARPS)[root % 12] + quality)
    return out


if __name__ == '__main__':
    assert roman('I V vi IV', 'D') == ['D', 'A', 'Bm', 'G']
    assert roman('i bVI bIII bVII', 'd') == ['Dm', 'Bb', 'F', 'C']
    assert roman('I bVII IV I', 'G') == ['G', 'F', 'C', 'G']
    assert roman('ii7 V7 Imaj7', 'C') == ['Dm7', 'G7', 'Cmaj7']
    assert roman('i iv V vii°', 'a') == ['Am', 'Dm', 'E', 'G#dim']
    assert stack('Bm', 'g3') == [midi('b3'), midi('d4'), midi('f#4')]
    assert above('Bm', 'c2') == midi('b2') and above('Bm', 'c2', 2) == midi('f#2')
    assert transpose('Bm', 2) == 'C#m' and transpose('Bb', 2) == 'C'
    print('theory ok')
