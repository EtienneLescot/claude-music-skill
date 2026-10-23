"""The orchestra: a score asks for an instrument and an articulation; the orchestra picks the source, the seat (pan),
the room send and a level calibrated so the same score balances the same way in both modes.

    open      Sonatina Symphonic Orchestra 4.0 (CC Sampling Plus) for strings, brass, woodwinds, harp, timpani and
              drums; VSCO 2 Community Edition (CC0) for the big drum, tenor drum, anvil, timpani rolls and cymbal
              swell; played by sfizz. Installed by setup.py, no account.
    discover  BBC Symphony Orchestra Discover for what it has (strings, brass, percussion), see discover.py.

The choir is sung in both modes by DiffSinger voices (sing.py); harp, flute and the sub come from the open sources.

    orch = Orchestra()                   # MUSIC_STUDIO_MODE=open|discover, else discover when it is set up
    hn = orch.part('horns', 'long')
    hn.line(0, [('d4', 3), ('a4', 3)], vel=110); hn.expr((0, 90), (6, 120))
    orch.render('tracks/slug.wav', eighth=60 / 110 / 3)
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import discover  # noqa: E402
from studio import HOME, Part, percussion, render, synth, timpani_rolls  # noqa: E402

SSO = HOME / 'sso' / 'Sonatina Symphonic Orchestra'
VSCO = HOME / 'vsco'
STR, BR, PERC, WW = 'Strings - Performance/', 'Brass - Performance/', 'Percussion/', 'Woodwinds - Performance/'
# the VSCO 2 files the catalog plays, (folder, pattern): all setup.py downloads from VSCO
ROLLS = ('Percussion/Timpani/Rolls', 'Timpani*_Roll_*.wav')
GIANT = ('VSCO 1 Percussion/drums/other/ethnic/giant/sticks', 'EthnicLargeSticks_hit_*.wav')
TENOR = ('VSCO 1 Percussion/drums/tenor/tenor_higher', 'tenorH_*.wav')
SWELL = ('VSCO 1 Percussion/varMetal/Cymbals/susp', 'susp_hit_softmall_roll2_cresc.wav')
BRAKE = ('VSCO 1 Percussion/varMetal/various', 'brake*.wav')
VSCO_FILES = [ROLLS, GIANT, TENOR, SWELL, BRAKE]


def _vsco_hits(files, release, name):
    return lambda: percussion(VSCO / files[0], files[1], release, name)


def _choir(section):
    def make():
        from sing import Choir                     # onnxruntime and the voices only for scores with a choir
        return Choir(section)
    return make


# (instrument, articulation): (open source, key, level dB, high-pass Hz, pan, room send, Discover seat or None).
# Open source: a Sonatina patch (long patches take their volume from CC1, shorts from velocity), or a function that
# builds the sound. Key: the key untuned percussion plays. Discover seat: (state, keyswitch, level dB).
# Levels were set by ear on the same score in both modes; Discover's sections play hotter.
CATALOG = {
    ('violins', 'long'): (STR + '1st Violins Legato.sfz', None, -9, None, -0.45, 0.3, ('violins1', 0, -1)),
    ('violins', 'short'): (STR + '1st Violins Staccato.sfz', None, -6, None, -0.45, 0.22, ('violins1', 1, -6)),
    ('violins', 'tremolo'): (STR + '1st Violins Tremolo.sfz', None, 8, None, -0.45, 0.35, ('violins1', 3, -3)),
    ('violins 2', 'long'): (STR + '2nd Violins Legato.sfz', None, -9, None, -0.2, 0.3, ('violins2', 0, -1)),
    ('violins 2', 'short'): (STR + '2nd Violins Staccato.sfz', None, -6, None, -0.2, 0.22, ('violins2', 1, -6)),
    ('violas', 'long'): (STR + 'Violas Legato.sfz', None, -6, 80, 0.15, 0.3, ('violas', 0, -8)),
    ('violas', 'short'): (STR + 'Violas Staccato.sfz', None, -8, 100, 0.15, 0.2, ('violas', 1, -11)),
    ('violas', 'tremolo'): (STR + 'Violas Tremolo.sfz', None, 8, 80, 0.15, 0.35, ('violas', 3, -6)),
    ('celli', 'long'): (STR + 'Celli Legato.sfz', None, -3, None, 0.35, 0.28, ('celli', 0, -5)),
    ('celli', 'short'): (STR + 'Celli Staccato.sfz', None, -3, None, 0.35, 0.18, ('celli', 1, -7)),
    ('celli', 'tremolo'): (STR + 'Celli Tremolo.sfz', None, 14, None, 0.35, 0.35, ('celli', 3, -3)),
    ('basses', 'long'): (STR + 'Basses Legato.sfz', None, -4, None, 0.5, 0.15, ('basses', 0, -8)),
    ('basses', 'short'): (STR + 'Basses Staccato.sfz', None, -4, None, 0.5, 0.15, ('basses', 1, -9)),
    ('horns', 'long'): (BR + 'Horns Legato.sfz', None, -2, 60, -0.2, 0.38, ('horns', 0, -10)),
    ('horns', 'short'): (BR + 'Horns Staccato.sfz', None, -1, None, -0.2, 0.35, ('horns', 1, -5)),
    ('trumpets', 'long'): (BR + 'Trumpets Legato.sfz', None, 6, 150, 0.05, 0.35, ('trumpets', 0, -4)),
    ('trumpets', 'short'): (BR + 'Trumpets Staccato.sfz', None, 2, 150, 0.05, 0.32, ('trumpets', 1, -4)),
    ('trombones', 'long'): (BR + 'Trombones Legato.sfz', None, -2, 50, 0.25, 0.33, ('trombones', 0, -8)),
    ('trombones', 'short'): (BR + 'Trombones Staccato.sfz', None, -5, 40, 0.25, 0.25, ('trombones', 1, -6)),
    ('bass trombones', 'long'): (BR + 'Bass Trombone Solo Sustain.sfz', None, 0, 35, 0.3, 0.3, ('basstrombones', 0, -8)),
    ('bass trombones', 'short'): (BR + 'Bass Trombone Solo Staccato.sfz', None, -3, 35, 0.3, 0.25,
                                  ('basstrombones', 1, -6)),
    ('tuba', 'long'): (BR + 'Tuba Legato.sfz', None, -6, None, 0.35, 0.22, ('tuba', 0, -6)),
    ('tuba', 'short'): (BR + 'Tuba Staccato.sfz', None, -9, None, 0.35, 0.2, ('tuba', 1, -7)),
    ('timpani', 'hit'): (PERC + 'Timpani.sfz', None, -7, None, 0.0, 0.25, ('percussion', 0, -8)),
    ('timpani', 'roll'): (lambda: timpani_rolls(VSCO / ROLLS[0]), None, 18, None, 0.0, 0.3,
                          ('percussion', 0, -16)),
    ('bass drum', 'hit'): (PERC + 'Bass Drum & Snare.sfz', 48, -1, None, 0.05, 0.2, ('percussion', 1, -4)),
    ('snare', 'hit'): (PERC + 'Bass Drum & Snare.sfz', 49, 0, 100, 0.05, 0.25, ('percussion', 1, -6)),
    ('cymbals', 'hit'): (PERC + 'Cymbals & Tamtam.sfz', 55, -6, None, -0.1, 0.35, ('percussion', 1, 0)),
    ('big drum', 'hit'): (_vsco_hits(GIANT, 1.5, 'giant'), 60, 6, 30, -0.05, 0.2, ('percussion', 1, -4)),
    ('tenor drum', 'hit'): (_vsco_hits(TENOR, 0.6, 'tenor'), 60, 0, 80, 0.15, 0.22, ('percussion', 1, -6)),
    ('cymbals', 'swell'): (_vsco_hits(SWELL, 3, 'swell'), 60, 6, None, 0.15, 0.4, ('percussion', 1, -6)),
    ('anvil', 'hit'): (_vsco_hits(BRAKE, 1.0, 'brake'), 60, 6, 300, -0.25, 0.3, ('percussion', 1, 0)),
    ('harp', 'short'): ('Concert Harp.sfz', None, -11, None, -0.35, 0.35, None),
    ('flute', 'long'): (WW + 'Flute Solo 1 Legato.sfz', None, -4, 200, -0.1, 0.35, None),
    ('choir', 'sopranos'): (_choir('sopranos'), None, -3, 180, -0.3, 0.4, None),
    ('choir', 'altos'): (_choir('altos'), None, -2, 150, -0.1, 0.4, None),
    ('choir', 'tenors'): (_choir('tenors'), None, 5, 100, 0.1, 0.4, None),
    ('choir', 'basses'): (_choir('basses'), None, 10, 60, 0.3, 0.4, None),
    ('sub', 'long'): (lambda: synth('sub', ampeg_attack=0.03, ampeg_release=0.5), None, -14, None, 0.0, 0.0, None),
}


class Orchestra:
    def __init__(self, mode=None):
        mode = mode or os.environ.get('MUSIC_STUDIO_MODE', 'auto')
        if mode == 'discover' and not discover.ready():
            sys.exit('Discover mode asked, but BBC Symphony Orchestra Discover or its states are missing: see setup.py')
        self.mode = 'discover' if mode == 'discover' or (mode == 'auto' and discover.ready()) else 'open'
        self.parts = []
        print(f'orchestra: {self.mode} mode')

    def part(self, instrument, articulation='long', name=None, **mix):
        """A Part for an instrument and articulation, seated and calibrated; mix overrides pan, send, gain, hpf, eq,
        fx."""
        if (instrument, articulation) not in CATALOG:
            sys.exit(f'unknown ({instrument}, {articulation}); known: {", ".join(f"{i} {a}" for i, a in sorted(CATALOG))}')
        source, key, level, hpf, pan, send, seat = CATALOG[(instrument, articulation)]
        name = name or f'{instrument}-{articulation}'.replace(' ', '-')
        if self.mode == 'discover' and seat:
            p = discover.part(name, instrument, articulation, seat)
            p.pan = pan
        else:
            p = Part(name, SSO / source if isinstance(source, str) else source(), pan=pan, gain=level, send=send, hpf=hpf)
            p.key = key
            p.needs_cc1 = isinstance(source, str) and articulation == 'long'   # silent without CC1
        for k, v in mix.items():
            setattr(p, k, v)
        self.parts.append(p)
        return p

    def render(self, out, eighth, master_fx=(), glue=(-14, 2), **hall):
        """Render every part made by this orchestra. Discover has its own room, so its hall is shorter."""
        if self.mode == 'discover':
            discover.adapt(self.parts, eighth)
        hall.setdefault('Decay', 2.2 if self.mode == 'discover' else 2.6)
        for p in self.parts:
            if getattr(p, 'needs_cc1', False) and not p.curve:
                p.expr((0, 100))
        return render(self.parts, out, eighth=eighth, master_fx=master_fx, glue=glue, **hall)


if __name__ == '__main__':
    for (i, a), entry in sorted(CATALOG.items()):
        print(f'  {i:<16} {a:<9} {"discover or open" if entry[6] else "sung, both modes" if i == "choir" else "open"}')
