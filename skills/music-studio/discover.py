"""BBC Symphony Orchestra Discover (Spitfire Audio), the optional sound source: real sections recorded together at
Maida Vale, in one hall. Free with a Spitfire account, installed by the user through the Spitfire Audio app; the
studio hosts the plugin headless with DawDreamer and picks articulations with keyswitches.

Choosing an instrument is not a plugin parameter and the presets are encrypted, so each user saves one state per
instrument, once (capture). The states hold Spitfire's patch data, which its licence (clauses 5 and 8) does not let
a project redistribute: they stay on the user's machine, in STUDIO_HOME/discover."""
import os
import re
import sys
from pathlib import Path

import numpy as np

from studio import HOME, VST, Part

PLUGIN = {'nt': r'C:\Program Files\Common Files\VST3\BBC Symphony Orchestra (64 Bit).vst3',
          'posix': '/Library/Audio/Plug-Ins/VST3/BBC Symphony Orchestra.vst3'}
STATES = HOME / 'discover'
# state name -> the name the plugin shows in its preset list
PRESETS = {'violins1': 'Violins 1', 'violins2': 'Violins 2', 'violas': 'Violas', 'celli': 'Celli', 'basses': 'Basses',
           'horns': 'Horns a4', 'trumpets': 'Trumpets a3', 'trombones': 'Tenor Trombones a3',
           'basstrombones': 'Bass Trombones a2', 'tuba': 'Tuba', 'percussion': 'Percussion'}
# keyswitches: strings 0 long, 1 spiccato, 3 tremolo; brass 0 long, 1 staccatissimo; percussion 0 timpani,
# 1 untuned, where each instrument sits on one key (measured)
KEY = {'bass drum': 48, 'big drum': 48, 'tenor drum': 50, 'snare': 52, 'cymbals': 71, 'anvil': 57}
SWELL_KEY = 53                                         # suspended cymbal: a swell becomes strokes, louder and louder
SWELL_PEAK = 3.31                                      # seconds from the start of a swell to its peak, as in open mode
TIMPANI_SHIFT = 12                                     # Discover's timpani sound an octave above the open ones


def plugin():
    path = Path(os.environ.get('BBCSO_VST3', PLUGIN.get(os.name, '')))
    return path if path.exists() else None


def state(name):
    f = STATES / f'{name}.state'
    return f if f.exists() else None


def ready():
    return bool(plugin() and state('violins1'))


def part(name, instrument, articulation, seat):
    """A Part played by Discover. seat: (state, keyswitch, level dB) from the orchestra's catalog."""
    st, ks, level = seat
    p = Part(name, VST(plugin(), state(st)), send=0.08, gain=level)
    p.keyswitch = ks
    if st == 'percussion' and ks == 1:
        p.key = SWELL_KEY if articulation == 'swell' else KEY[instrument]
    p.discover = (instrument, articulation)
    return p


def adapt(parts, eighth):
    """What Discover plays differently: timpani an octave up, rolls as fast hits (it has no roll samples), swells
    as cymbal strokes growing for SWELL_PEAK seconds."""
    for p in parts:
        instrument, articulation = getattr(p, 'discover', (None, None))
        if instrument == 'timpani':
            p.notes = [(t, d, k + TIMPANI_SHIFT, v) for t, d, k, v in p.notes]
        if articulation == 'roll':                     # four hits per eighth; the fader shape becomes velocity
            fader, notes = sorted(p.fader), p.notes
            p.notes, p.fader = [], []
            for t0, d, pitch, vel in notes:
                for k, t in enumerate(np.arange(t0, t0 + d, 0.25)):
                    level = np.interp(t, [f[0] for f in fader], [f[1] for f in fader]) if fader else 0.0
                    p.note(t, 0.3, pitch, min(vel, 40 + 85 * 10 ** (level / 40)) + (6 if k % 2 else 0))
        if articulation == 'swell':
            notes, p.notes = p.notes, []
            n = int(SWELL_PEAK / eighth * 4)
            for t0, _, _, vel in notes:
                for k in range(n):
                    p.note(t0 + k / 4, 0.3, SWELL_KEY, 30 + (vel - 30) * (k / n) ** 1.5)


def state_instrument(path):
    """The instrument a saved state holds. The state is JUCE's VST3 XML; its IComponent is JUCE base64, holding
    Spitfire's own XML whose META tag names the preset."""
    raw = Path(path).read_bytes()
    enc = re.search(rb'<IComponent>(\d+)\.([^<]*)</IComponent>', raw)
    chars = '.ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+'
    out = bytearray(int(enc[1]))
    for i, c in enumerate(enc[2].decode()):
        v = chars.index(c)
        for b in range(6):
            if v >> b & 1 and (i * 6 + b) // 8 < len(out):
                out[(i * 6 + b) // 8] |= 1 << ((i * 6 + b) % 8)
    m = re.search(rb'name="Discover - ([^"]+)"', out)
    return m and m[1].decode()


def capture(names=None):
    """One plugin window per instrument: choose the instrument named on screen, click Load, close the window; the
    state is saved and checked, and asked again if it holds another instrument. The user does this, not the agent:
    the plugin's window is the only way to choose an instrument."""
    import dawdreamer as dd
    if not plugin():
        sys.exit('BBC Symphony Orchestra Discover is not installed')
    STATES.mkdir(parents=True, exist_ok=True)
    for name in names or PRESETS:
        want = PRESETS[name]
        while True:
            p = dd.RenderEngine(48000, 512).make_plugin_processor('bbc', str(plugin()))
            print(f'{name}: in the window, open the preset list, choose "{want}", click Load, close the window')
            p.open_editor()
            p.save_state(str(STATES / f'{name}.state'))
            got = state_instrument(STATES / f'{name}.state')
            if got == want:
                print(f'  saved {name} ({got})')
                break
            print(f'  that window held "{got}", not "{want}": once more')


def report():
    have = sorted(p.stem for p in STATES.glob('*.state')) if STATES.exists() else []
    print(f'BBC Symphony Orchestra Discover: {"installed" if plugin() else "not installed"}; '
          f'states: {have or "none"}{"" if set(PRESETS) <= set(have) else " (setup.py --capture)" if plugin() else ""}')
