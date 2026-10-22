"""The orchestra: one score, two sound sources.

    open      free sample files (VSCO 2 Community Edition, CC0; Virtual Playing Orchestra, free) played by sfizz.
              Installed by setup.py with no account. Sounds like a good mockup.
    discover  BBC Symphony Orchestra Discover (Spitfire Audio, free with an account) hosted by DawDreamer:
              real sections recorded together in one hall. Clearly better; the user installs it once.

A score asks for instruments by name and articulation; the orchestra picks the source, the seat (pan), the room
send and a level calibrated so a score balances the same way in both modes. Instruments Discover lacks (choirs,
harp, flute, synths) come from the open libraries in both modes.

    orch = Orchestra()                         # mode: MUSIC_STUDIO_MODE=open|discover, else discover when installed
    hn = orch.part('horns', 'long')
    hn.line(0, [('d4', 3), ('a4', 3)], vel=110); hn.expr((0, 90), (6, 120))
    orch.render('tracks/slug.wav', eighth=60 / 110 / 3)
"""
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio import HOME, VPO, VST, Part, decent, instrument, percussion, render, synth, timpani  # noqa: E402

HERE = Path(__file__).resolve().parent
PLUGIN = {'nt': r'C:\Program Files\Common Files\VST3\BBC Symphony Orchestra (64 Bit).vst3',
          'posix': '/Library/Audio/Plug-Ins/VST3/BBC Symphony Orchestra.vst3'}
STATES = [HERE / 'discover', HOME / 'discover']           # shipped states, then states captured on this machine

S, X = 'sus', 'short'
# (instrument, articulation): open source, its options, open level, Discover (state, keyswitch, level), pan, send.
# Levels in dB were set by ear on the same score in both modes; Discover's sections play 5 to 12 dB hotter.
CATALOG = {
    ('violins', 'long'): (lambda: instrument('Strings/Violin Section/susVib', S, 0.5, legato=True),
                          dict(ensemble=3, eq=[(3000, 2, 0.8)]), 10, ('violins1', 0, -1), -0.45, 0.3),
    ('violins', 'short'): (lambda: instrument('Strings/Violin Section/Spic', X, 0.25), {}, 0, ('violins1', 1, -6), -0.45, 0.22),
    ('violins', 'tremolo'): (lambda: instrument('Strings/Violin Section/Trem', S, 0.6), {}, 0, ('violins1', 3, -3), -0.45, 0.35),
    ('violins 2', 'long'): (lambda: instrument('Strings/Violin Section/susVib', S, 0.5, legato=True),
                            dict(ensemble=3), 8, ('violins2', 0, -1), -0.2, 0.3),
    ('violins 2', 'short'): (lambda: instrument('Strings/Violin Section/Spic', X, 0.25), {}, 0, ('violins2', 1, -6), -0.2, 0.22),
    ('violas', 'long'): (lambda: instrument('Strings/Viola Section/susvib', S, 0.5, legato=True),
                         dict(ensemble=2, hpf=80), 2, ('violas', 0, -8), 0.15, 0.3),
    ('violas', 'short'): (lambda: instrument('Strings/Viola Section/spic', X, 0.25), dict(hpf=100), -2, ('violas', 1, -11), 0.15, 0.2),
    ('violas', 'tremolo'): (lambda: instrument('Strings/Viola Section/trem', S, 0.6), dict(hpf=80), 0, ('violas', 3, -6), 0.15, 0.35),
    ('celli', 'long'): (lambda: instrument('Strings/Cello Section/susvib', S, 0.5, legato=True), {}, 0, ('celli', 0, -5), 0.35, 0.28),
    ('celli', 'short'): (lambda: instrument('Strings/Cello Section/spic', X, 0.25), dict(eq=[(2500, 2, 1.0)]), 2,
                         ('celli', 1, -7), 0.35, 0.18),
    ('celli', 'tremolo'): (lambda: instrument('Strings/Cello Section/trem', S, 0.6), {}, 0, ('celli', 3, -3), 0.35, 0.35),
    ('basses', 'long'): (lambda: decent(VPO / 'bass-SEC-sustain.dspreset', 0.8), {}, 2, ('basses', 0, -8), 0.5, 0.15),
    ('basses', 'short'): (lambda: decent(VPO / 'bass-SEC-staccato.dspreset', 0.3), {}, 0, ('basses', 1, -9), 0.5, 0.15),
    ('horns', 'long'): (lambda: instrument('Brass/F Horn/sus', S, 0.5, legato=True),
                        dict(ensemble=6, hpf=60, eq=[(2200, 2.5, 1.0)]), 4, ('horns', 0, -10), -0.2, 0.38),
    ('horns', 'short'): (lambda: instrument('Brass/F Horn/stac', X, 0.3), dict(ensemble=4), 0, ('horns', 1, -5), -0.2, 0.35),
    ('trumpets', 'long'): (lambda: instrument('Brass/Trumpet/sus', S, 0.4, legato=True), dict(ensemble=3, hpf=150), 0,
                           ('trumpets', 0, -4), 0.05, 0.35),
    ('trumpets', 'short'): (lambda: instrument('Brass/Trumpet/stac', X, 0.3), dict(ensemble=2, hpf=150), 8,
                            ('trumpets', 1, -4), 0.05, 0.32),
    ('trombones', 'long'): (lambda: instrument('Brass/Tenor Trombone/sus', S, 0.5, legato=True),
                            dict(ensemble=4, hpf=50, eq=[(1800, 2, 1.0)]), 12, ('trombones', 0, -8), 0.25, 0.33),
    ('trombones', 'short'): (lambda: instrument('Brass/Tenor Trombone/stac', X, 0.3), dict(ensemble=3, hpf=40), 4,
                             ('trombones', 1, -6), 0.25, 0.25),
    ('bass trombones', 'long'): (lambda: instrument('Brass/Tenor Trombone/sus', S, 0.5), dict(ensemble=2, hpf=35), 10,
                                 ('basstrombones', 0, -8), 0.3, 0.3),
    ('bass trombones', 'short'): (lambda: instrument('Brass/Tenor Trombone/stac', X, 0.3), dict(ensemble=2, hpf=35), 4,
                                  ('basstrombones', 1, -6), 0.3, 0.25),
    ('tuba', 'long'): (lambda: instrument('Brass/Tuba/sus', S, 0.5), {}, 4, ('tuba', 0, -6), 0.35, 0.22),
    ('tuba', 'short'): (lambda: instrument('Brass/Tuba/stac', X, 0.3), {}, 8, ('tuba', 1, -7), 0.35, 0.2),
    ('timpani', 'hit'): (lambda: timpani(), {}, 8, ('percussion', 0, -8), 0.0, 0.25),
    ('timpani', 'roll'): (lambda: timpani('Percussion/Timpani/Rolls', 'Roll', release=1.0, veltrack=80), {}, 18,
                          ('percussion', 0, -16), 0.0, 0.3),
    ('bass drum', 'hit'): (lambda: percussion('VSCO 1 Percussion/drums/bass', 'bdrum_*.wav', 1.5, name='bd'), {}, 2,
                           ('percussion', 1, -4), 0.05, 0.2),
    ('big drum', 'hit'): (lambda: percussion('VSCO 1 Percussion/drums/other/ethnic/giant/sticks', 'EthnicLargeSticks_hit_*.wav',
                                             1.5, name='giant'), dict(hpf=30), 6, ('percussion', 1, -4), -0.05, 0.2),
    ('snare', 'hit'): (lambda: percussion('VSCO 1 Percussion/drums/snare/drum1', 'snare1_[fmp]*.wav', 0.5, name='sn'),
                       dict(hpf=100), -4, ('percussion', 1, -6), 0.05, 0.25),
    ('tenor drum', 'hit'): (lambda: percussion('VSCO 1 Percussion/drums/tenor/tenor_higher', 'tenorH_*.wav', 0.6, name='tenor'),
                            dict(hpf=80), 0, ('percussion', 1, -6), 0.15, 0.22),
    ('cymbals', 'hit'): (lambda: percussion('VSCO 1 Percussion/varMetal/Cymbals/clash', 'crash_hit_*.wav', 3, name='crash'),
                         {}, 2, ('percussion', 1, 0), -0.1, 0.35),
    ('cymbals', 'swell'): (lambda: percussion('VSCO 1 Percussion/varMetal/Cymbals/susp', 'susp_hit_softmall_roll2_cresc.wav',
                                              3, name='swell'), {}, 6, ('percussion', 1, -6), 0.15, 0.4),
    ('anvil', 'hit'): (lambda: percussion('VSCO 1 Percussion/varMetal/various', 'brake*.wav', 1.0, name='brake'),
                       dict(hpf=300), 6, ('percussion', 1, 0), -0.25, 0.3),
    ('harp', 'short'): (lambda: instrument('Strings/Harp', X, 1.5, octave=0), {}, 6, None, -0.35, 0.35),
    ('flute', 'long'): (lambda: instrument('Woodwinds/Flute/susvib', S, 0.5, legato=True), dict(hpf=200), 6, None, -0.1, 0.35),
    ('choir', 'long'): (lambda: decent(VPO / 'choir-MIXED-sustain.dspreset', 1.2), dict(hpf=150), 1, None, 0.0, 0.45),
    ('male choir', 'long'): (lambda: decent(VPO / 'choir-MALE-normal-mod-wheel.dspreset', 1.2), dict(hpf=80), 4, None, 0.1, 0.45),
    ('sub', 'long'): (lambda: synth('sub', ampeg_attack=0.03, ampeg_release=0.5), {}, -14, None, 0.0, 0.0),
}
# Discover's untuned percussion sits on one keyboard (measured): every hit plays its instrument's key
DISCOVER_KEY = {'bass drum': 48, 'big drum': 48, 'tenor drum': 50, 'snare': 52, 'cymbals': 71, 'anvil': 57}
SWELL_KEY = 53                                         # suspended cymbal: a swell becomes strokes, louder and louder
TIMPANI_SHIFT = 12                                     # Discover's timpani sound an octave above the open ones
SWELL_PEAK = 3.31                                      # seconds from the start of the open cymbal swell to its peak


def discover_plugin():
    path = Path(os.environ.get('BBCSO_VST3', PLUGIN.get(os.name, '')))
    return path if path.exists() else None


def discover_state(name):
    return next((d / f'{name}.state' for d in STATES if (d / f'{name}.state').exists()), None)


def articulations():
    """Every instrument and articulation the catalog knows, for the skill's reference."""
    return sorted(CATALOG)


class Orchestra:
    def __init__(self, mode=None):
        mode = mode or os.environ.get('MUSIC_STUDIO_MODE', 'auto')
        has = discover_plugin() and discover_state('violins1')
        if mode == 'discover' and not has:
            sys.exit('Discover mode asked, but BBC Symphony Orchestra Discover or its states are missing: see setup.py')
        self.mode = 'discover' if (mode == 'discover' or (mode == 'auto' and has)) else 'open'
        self.parts, self.rolls, self.swells = [], [], []
        print(f'orchestra: {self.mode} mode')

    def part(self, instrument_name, articulation='long', name=None, **mix):
        """A Part for an instrument and articulation, seated and calibrated; mix overrides pan, send, gain…"""
        key = (instrument_name, articulation)
        if key not in CATALOG:
            sys.exit(f'unknown {key}; known: {", ".join(f"{i} {a}" for i, a in articulations())}')
        source, options, gain, disc, pan, send = CATALOG[key]
        name = name or f'{instrument_name}-{articulation}'.replace(' ', '-')
        if self.mode == 'discover' and disc:
            state, ks, dgain = disc
            p = Part(name, VST(discover_plugin(), discover_state(state)), pan=pan, send=0.08, gain=dgain)
            p.keyswitch = ks
            if state == 'percussion' and ks == 1:
                p.key = SWELL_KEY if articulation == 'swell' else DISCOVER_KEY[instrument_name]
            p.timpani = instrument_name == 'timpani'
            if articulation == 'roll':
                self.rolls.append(p)
            if articulation == 'swell':
                self.swells.append(p)
        else:
            p = Part(name, source(), pan=pan, send=send, gain=gain, **options)
            if instrument_name in DISCOVER_KEY or articulation == 'swell':
                p.key = 60                                  # the open percussion SFZs sit on one key
        for k, v in mix.items():
            setattr(p, k, v)
        self.parts.append(p)
        return p

    def _discover_fixes(self, eighth):
        """What Discover plays differently: timpani an octave up, rolls as fast hits, swells as cymbal strokes."""
        for p in self.parts:
            if getattr(p, 'timpani', False):
                p.notes = [(t, d, k + TIMPANI_SHIFT, v) for t, d, k, v in p.notes]
        for p in self.rolls:                               # four hits per eighth; the fader shape becomes velocity
            fader, notes = sorted(p.fader), p.notes
            p.notes, p.fader = [], []
            for t0, d, pitch, vel in notes:
                for k, t in enumerate(np.arange(t0, t0 + d, 0.25)):
                    level = np.interp(t, [f[0] for f in fader], [f[1] for f in fader]) if fader else 0.0
                    p.note(t, 0.3, pitch, min(vel, 40 + 85 * 10 ** (level / 40)) + (6 if k % 2 else 0))
        for p in self.swells:                              # strokes growing for SWELL_PEAK seconds
            notes, p.notes = p.notes, []
            n = int(SWELL_PEAK / eighth * 4)
            for t0, _, _, vel in notes:
                for k in range(n):
                    p.note(t0 + k / 4, 0.3, SWELL_KEY, 30 + (vel - 30) * (k / n) ** 1.5)

    def render(self, out, eighth, master_fx=(), glue=(-14, 2), **hall):
        """Render every part made by this orchestra. The hall is shorter in Discover mode, which has its own room."""
        if self.mode == 'discover':
            self._discover_fixes(eighth)
            hall.setdefault('Decay', 2.2)
        else:
            hall.setdefault('Decay', 2.6)
        return render(self.parts, out, eighth=eighth, master_fx=master_fx, glue=glue, **hall)


if __name__ == '__main__':
    print('discover plugin:', discover_plugin() or 'not installed')
    print('discover states:', [p.stem for d in STATES if d.exists() for p in sorted(d.glob('*.state'))] or 'none')
    for i, a in articulations():
        print(f'  {i:<16} {a:<8} {"discover" if CATALOG[(i, a)][3] else "open only"}')
