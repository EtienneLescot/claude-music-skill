"""Electronic instruments for the studio: Surge XT factory patches hosted headless by DawDreamer, plus synthesized
percussion and FX (ticks, shaker, 808 hats, risers, booms, sub swells), Moog ladder filter sweeps on part.expr, and
sidechain pumping from the kicks.

    python surge.py list Basses             # factory patch names, to choose from
    from surge import boom, chain, cut, hat, riser, shaker, surge, swell, synth, tick
    kick = Part('kick', surge('Percussion/Kick Tech 1'), gain=-2, send=0.02)
    bass = Part('bass', chain(surge('Basses/Dist Bass 1'), kicks=[kick]), gain=0, send=0.0)
    bass.duck = 6                                                      # 6 dB sidechain dip on every kick
    lead = Part('motif', chain(surge('Plucks/Saw Pluck'), kicks=[kick]), gain=5, send=0.15)
    lead.sweep, lead.duck = True, 4                                    # expr curve drives a 24 dB ladder low-pass
    lead.expr((0, cut(500)), (48, cut(4500)))
    hats = Part('hats', synth(hat), pan=0.1, gain=-3, send=0.05)
"""
import functools
import json
import os
import re
import struct
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pedalboard as pb
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio import HOME, SR, TOOLS  # noqa: E402

DIR = HOME / 'surge'
SOURCE = 'https://raw.githubusercontent.com/surge-synthesizer/surge/release_xt_1.3.4/resources/data/patches_factory/'
PRE = 0.5                                       # seconds of pre-roll: Surge drops a note at time 0
TABLE = '.ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+'     # JUCE's base64 alphabet
HATF = np.array([263, 400, 421, 474, 587, 845]) * 2.0          # the 808's six detuned squares, an octave up


@functools.cache
def plugin():
    """Surge XT's VST3: setup.py's download, else a system install."""
    common = Path(os.environ.get('COMMONPROGRAMFILES', 'C:/Program Files/Common Files'))
    for d in (TOOLS, HOME / 'plugins', common / 'VST3', Path.home() / 'Library/Audio/Plug-Ins/VST3',
              Path('/Library/Audio/Plug-Ins/VST3'), Path.home() / '.vst3', Path('/usr/lib/vst3')):
        found = sorted(d.rglob('Surge XT.vst3')) if d.exists() else []
        if found:
            return found[0]


def b64(data):
    """JUCE MemoryBlock::toBase64Encoding: the size, a dot, then 6-bit groups read from the least significant bit."""
    bits = np.unpackbits(np.frombuffer(data, np.uint8), bitorder='little')
    bits = np.pad(bits, (0, -len(bits) % 6)).reshape(-1, 6)
    return f'{len(data)}.' + ''.join(TABLE[i] for i in bits @ (1 << np.arange(6)))


def unb64(text):
    size, body = text.split('.', 1)
    bits = ((np.array([TABLE.index(c) for c in body])[:, None] >> np.arange(6)) & 1).astype(np.uint8).ravel()
    return np.packbits(bits[:int(size) * 8], bitorder='little').tobytes()


def _template():
    """A state saved from a fresh Surge XT: JUCE's 'VC2!' header and the VST3 XML around the plugin's own data."""
    path = DIR / 'default.state'
    if not path.exists():
        import dawdreamer as dd
        vst = plugin() or sys.exit('Surge XT.vst3 not found: run setup.py first')
        DIR.mkdir(parents=True, exist_ok=True)
        eng = dd.RenderEngine(SR, 256)                     # the processor dies with its engine: keep it alive
        eng.make_plugin_processor('surge', str(vst)).save_state(str(path))
    return path.read_bytes()[8:].rstrip(b'\0').decode()


def state(patch):
    """The state file for a factory patch such as 'Basses/Rumble': the .fxp minus its 60-byte header is exactly what
    Surge saves as its own state."""
    fxp = DIR / 'patches' / f'{patch}.fxp'
    if not fxp.exists():
        fxp.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(SOURCE + urllib.parse.quote(f'{patch}.fxp'), fxp)
    raw = fxp.read_bytes()
    assert raw[:4] == b'CcnK' and raw[60:64] == b'sub3', f'{fxp}: not a Surge patch'
    xml = re.sub(r'<IComponent>.*?</IComponent>', lambda m: f'<IComponent>{b64(raw[60:])}</IComponent>', _template(),
                 flags=re.S).encode()
    out = DIR / 'states' / f'{patch.replace("/", "-")}.state'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b'VC2!' + struct.pack('<I', len(xml)) + xml + b'\0')
    return out


def surge(patch, tail=3.0):
    """A Part sound that plays a Surge XT factory patch, every note on the grid (no humanizing: this is electronic)."""
    path = state(patch)
    vst = plugin() or sys.exit('Surge XT.vst3 not found: run setup.py first')

    def render(part, eighth, rng):
        import dawdreamer as dd
        eng = dd.RenderEngine(SR, 256)
        p = eng.make_plugin_processor(part.name, str(vst))
        p.load_state(str(path))
        for t, d, m, v in part.notes:                      # a note at time 0 is dropped: everything starts PRE late
            p.add_midi_note(int(round(m)), int(v), PRE + t * eighth, d * eighth)
        eng.load_graph([(p, [])])
        eng.render(PRE + max(t + d for t, d, _, _ in part.notes) * eighth + tail)
        return np.ascontiguousarray(eng.get_audio().T[int(PRE * SR):], dtype=np.float32)
    return render


# ---------------------------------------------------------------- DSP synthesis, filters and sidechain

def tt(n): return np.arange(n) / SR
def sos(*a): return signal.butter(*a, fs=SR, output='sos')
def hp(x, f, o=2): return signal.sosfilt(sos(o, f, 'hp'), x)
def lp(x, f, o=2): return signal.sosfilt(sos(o, f, 'lp'), x)
def bp(x, lo, hi, o=2): return signal.sosfilt(sos(o, [lo, hi], 'band'), x)
def sweep(f, n): return np.sin(2 * np.pi * np.cumsum(np.broadcast_to(f, (n,))) / SR)
def cut(hz): return 127 * np.log2(hz / 150) / 6.5          # a cutoff in Hz (150 Hz-13.5 kHz) as an expr value


def saw(f, n, ph0=0.0):
    """Band-limited saw (polyBLEP); f in Hz, a number or one value per sample."""
    dt = np.broadcast_to(np.asarray(f, float), (n,)) / SR
    ph = (ph0 + np.cumsum(dt)) % 1.0
    y = 2 * ph - 1
    lo = ph < dt
    u = ph[lo] / dt[lo]
    y[lo] -= u + u - u * u - 1
    hi = ph > 1 - dt
    u = (ph[hi] - 1) / dt[hi]
    y[hi] -= u * u + u + u + 1
    return y


def square(f, n, ph0=0.0):
    return saw(f, n, ph0) - saw(f, n, ph0 + 0.5)


def ladder(x, cut_hz, res=0.3, mode='LPF24', block=128):
    """Moog-style ladder filter whose cutoff (Hz, a number or one per sample) moves every block."""
    x = np.atleast_2d(x).astype(np.float32)
    n = x.shape[1]
    x = np.pad(x, ((0, 0), (0, -n % block)))
    cut_hz = np.broadcast_to(np.asarray(cut_hz, float), (n,))
    f = pb.LadderFilter(mode=getattr(pb.LadderFilter.Mode, mode), cutoff_hz=float(cut_hz[0]), resonance=res)
    out = np.empty_like(x)
    for i in range(0, x.shape[1], block):
        f.cutoff_hz = float(np.clip(cut_hz[min(i, n - 1)], 20, 18000))
        out[:, i:i + block] = f.process(x[:, i:i + block], SR, reset=i == 0)
    return out[:, :n]


def hat(f, dur, v, cut_hz, rng, decay=0.04):
    """808/909 metallic hi-hat: six detuned squares + high-passed noise (decay=0.04 closed, 0.09 open)."""
    n = int(min(10 * decay, 1.0) * SR)
    metal = sum(square(fr, n, rng.random()) for fr in HATF) / 6
    x = hp(bp(0.7 * metal + 0.5 * rng.standard_normal(n), 6000, 16000), 7000) * np.exp(-tt(n) / decay)
    p = rng.uniform(-0.4, 0.4)
    return np.stack([x * (1 - p), x * (1 + p)]) * v ** 1.5


def tick(f, dur, v, cut_hz, rng):
    """Filtered analog tick: a noise burst through a band-pass at cut_hz, a short ping on top, panned at random."""
    n = int(0.05 * SR)
    t = tt(n)
    x = bp(rng.standard_normal(n) * np.exp(-t / 0.004), cut_hz / 1.5, min(cut_hz * 1.5, 20000))
    x += 0.3 * np.sin(2 * np.pi * cut_hz * t) * np.exp(-t / 0.003)
    p = rng.uniform(-0.35, 0.35)
    return np.stack([x * (1 - p), x * (1 + p)]) * v ** 1.5


def shaker(f, dur, v, cut_hz, rng):
    """Soft brushed 16th-note shaker."""
    n = int(0.1 * SR)
    t = tt(n)
    return hp(rng.standard_normal((2, n)), 6000, 4) * (1 - np.exp(-t / 0.006)) * np.exp(-t / 0.03) * v ** 1.5


def boom(f, dur, v, cut_hz, rng, length=3.5):
    """Sub impact drop: a sine falling from 100 to 30 Hz under a dark noise crack."""
    n = int(length * SR)
    t = tt(n)
    sub = sweep(30 + 70 * np.exp(-t / 0.18), n) * np.exp(-t / 1.1)
    crack = lp(rng.standard_normal((2, n)), 2500) * np.exp(-t / 0.3)
    return np.tanh(1.8 * (sub + 0.6 * crack)) * v ** 1.5


def riser(f, dur, v, cut_hz, rng, grit=3.0):
    """Noise through a resonant band-pass sweeping 250 Hz-10 kHz, a saw climbing two octaves, distorted; stops dead."""
    n = int(dur * SR)
    u = tt(n) / dur
    track = 250 * 40 ** u
    noise = ladder(rng.standard_normal((2, n)), track, res=0.55, mode='BPF12')
    tone = ladder(saw(f * 4 ** u, n), track * 0.6, res=0.4)
    x = np.tanh(grit * (noise + 0.5 * tone)) * u ** 2.2
    x[:, -480:] *= np.linspace(1, 0, 480)
    return x * v ** 1.5


def swell(f, dur, v, cut_hz, rng):
    """Dark sub swell: rises for a second, then dies away."""
    n = int(dur * SR)
    t = tt(n)
    x = (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t))
    x *= (1 - np.exp(-t / 0.6)) * np.exp(-np.maximum(t - 1.2, 0) / 3.2)
    x[-2400:] *= np.linspace(1, 0, 2400)
    return x * v ** 1.5


def synth(voice, **kw):
    """A Part sound from a DSP voice function: every note rendered alone, its cutoff read from part.expr."""
    def render(part, eighth, rng):
        out = np.zeros((2, int((max(t + d for t, d, _, _ in part.notes) * eighth + 5) * SR)), np.float32)
        pts = sorted(part.curve)
        for t, d, p, vel in sorted(part.notes):
            cut_hz = 150 * 2 ** (6.5 * np.interp(t, *zip(*pts)) / 127) if pts else 1000.0
            x = np.atleast_2d(voice(440 * 2 ** ((p - 69) / 12), d * eighth, vel / 127, cut_hz, rng, **kw))
            i = int(t * eighth * SR)
            x = x[:, :out.shape[1] - i]
            out[:, i:i + x.shape[1]] += x
        return out.T
    return render


def pump(n, eighth, kicks, depth, recover=0.13):
    """Sidechain from the kick parts: gain drops by depth dB within 3 ms of every kick, then recovers over an eighth."""
    k = np.array(sorted(note[0] for p in kicks for note in p.notes)) * eighth
    if not len(k):
        return np.ones(n, np.float32)
    t = np.arange(n) / SR
    dt = t - k[np.maximum(np.searchsorted(k, t, side='right') - 1, 0)]
    dip = np.where(dt >= 0, np.exp(-dt / recover) * np.minimum(dt / 0.003, 1), 0)
    return (1 - (1 - 10 ** (-depth / 20)) * dip).astype(np.float32)


def chain(sound, kicks=()):
    """Wrap a Part sound so part.sweep=True applies a low-pass following part.expr, and part.duck=dB pumps on kicks."""
    def render(part, eighth, rng):
        x = sound(part, eighth, rng)
        if getattr(part, 'sweep', False) and part.curve:
            ts, vs = zip(*sorted(part.curve))
            hz = 150 * 2 ** (6.5 * np.interp(np.arange(len(x)) / SR / eighth, ts, vs) / 127)
            x = ladder(x.T, hz, res=0.15).T
        ks = getattr(part, 'kicks', None) or kicks
        if getattr(part, 'duck', 0) and ks:
            x = x * pump(len(x), eighth, ks, part.duck)[:, None]
        return x
    return render


def factory(category=''):
    """The factory patch names, 'Category/Patch', from Surge's repository: one request, nothing downloaded."""
    tree = json.loads(urllib.request.urlopen('https://api.github.com/repos/surge-synthesizer/surge/git/trees/'
                                             'release_xt_1.3.4?recursive=1', timeout=60).read())['tree']
    root = 'resources/data/patches_factory/'
    return [x['path'][len(root):-4] for x in tree
            if x['path'].startswith(root + category) and x['path'].endswith('.fxp')]


if __name__ == '__main__':
    if sys.argv[1:2] == ['list']:              # python surge.py list [Basses]
        for name in factory(sys.argv[2] if len(sys.argv) > 2 else ''):
            print(name)
        sys.exit()
    t = _template()                            # the template's plugin data decodes back to a Surge patch
    assert unb64(re.search(r'<IComponent>(.*?)</IComponent>', t, re.S)[1].strip())[:4] == b'sub3'
    assert unb64(b64(b'surge xt')) == b'surge xt'
    print('ok: template decodes to a Surge patch, base64 round-trips')
