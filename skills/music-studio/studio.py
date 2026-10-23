"""The studio engine. A score is Python that fills Parts with notes, expression curves and fader moves; render()
plays each part (an SFZ through sfizz, or a VST3 instrument through DawDreamer), mixes them with pedalboard and a
Dragonfly hall, and masters to -14 LUFS with a true-peak limiter. Time is counted in eighth notes.

    uv run --python 3.12 --with dawdreamer --with pedalboard --with mido --with numpy --with soundfile --with scipy \
        python studio.py --check

Most scores use orchestra.py on top of this, which picks the instruments. STUDIO_HOME (default ~/.music-studio)
holds what setup.py downloads: tools/ (sfizz, Dragonfly), sso/, vsco/ and vpo/ (sample libraries), voices/
(the sung choir, see sing.py)."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import mido
import numpy as np
import pedalboard as pb
import soundfile as sf
from numpy.lib.stride_tricks import sliding_window_view
from scipy import signal

HOME = Path(os.environ.get('STUDIO_HOME', Path.home() / '.music-studio'))
VSCO, VPO, TOOLS = HOME / 'vsco', HOME / 'vpo', HOME / 'tools'
SR = 48000
CEILING_DB = -1.0
PC = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}
DYN = ['ppp', 'pp', 'p', 'mp', 'mf', 'f', 'ff', 'fff']


def midi(name):
    """'bb4', 'c#5', 'a3' (scientific pitch, middle C = c4) to a MIDI number; numbers pass through."""
    if not isinstance(name, str):
        return name
    m = re.fullmatch(r'([a-g])(#|b)?(-?\d)', name.lower())
    return 12 * (int(m[3]) + 1) + PC[m[1]] + {'#': 1, 'b': -1, None: 0}[m[2]]


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def undb(d):
    return 10 ** (np.asarray(d) / 20)


def _tool(name):
    """A tool from setup.py's download, else from the PATH."""
    found = sorted(TOOLS.rglob(name)) if TOOLS.exists() else []
    path = found[0] if found else shutil.which(name.replace('.exe', ''))
    if not path:
        sys.exit(f'{name} not found: run setup.py first')
    return Path(path)


# ---------------------------------------------------------------- loudness (ITU-R BS.1770) and limiter

def _kweight(sr):
    K = np.tan(np.pi * 1681.974450955533 / sr)            # stage 1: +4 dB high shelf
    Q, Vh = 0.7071752369554196, 10 ** (3.999843853973347 / 20)
    Vb = Vh ** 0.4996667741545416
    a0 = 1 + K / Q + K * K
    shelf = [(Vh + Vb * K / Q + K * K) / a0, 2 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0,
             1, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]
    K = np.tan(np.pi * 38.13547087602444 / sr)            # stage 2: RLB high-pass
    Q = 0.5003270373238773
    a0 = 1 + K / Q + K * K
    return np.array([shelf, [1, -2, 1, 1, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]])


def lufs(x, sr=SR):
    """Integrated loudness: K-weighting, 400 ms blocks at 75 % overlap, absolute and relative gates."""
    y = signal.sosfilt(_kweight(sr), x.reshape(len(x), -1), axis=0)
    blk, hop = round(0.4 * sr), round(0.1 * sr)
    cs = np.vstack([np.zeros((1, y.shape[1])), np.cumsum(y ** 2, axis=0)])
    st = np.arange(1 + (len(y) - blk) // hop) * hop
    z = ((cs[st + blk] - cs[st]) / blk).sum(1)
    z = z[-0.691 + 10 * np.log10(z + 1e-20) > -70]
    if not len(z):
        return -120.0
    rel = -0.691 + 10 * np.log10(z.mean()) - 10
    return -0.691 + 10 * np.log10(z[-0.691 + 10 * np.log10(z) > rel].mean())


def true_peak(x, os_=4):
    return np.abs(signal.resample_poly(x, os_, 1, axis=0)).max()


def limiter(x, sr=SR, ceiling_db=CEILING_DB, look_ms=2.0, release_db_s=25.0, os_=4):
    """Look-ahead limiter on 4x-oversampled peaks; the gain reaches its target exactly at the peak."""
    n = len(x)
    xo = np.abs(signal.resample_poly(x, os_, 1, axis=0)).max(1)[:n * os_]
    tp = np.maximum(np.pad(xo, (0, n * os_ - len(xo))).reshape(n, os_).max(1), np.abs(x).max(1))
    g = np.minimum(1.0, undb(ceiling_db) / np.maximum(tp, 1e-9))
    L = int(look_ms * sr / 1000)
    g = sliding_window_view(np.r_[g, np.ones(L - 1)], L).min(1)
    k = np.arange(n) * (release_db_s / sr)
    g = undb(np.minimum(np.minimum.accumulate(db(g) - k) + k, 0))
    c = np.cumsum(np.r_[np.ones(L), g])
    g = (c[L:] - c[:-L]) / L
    return x * g[:, None], g


def loud(x, sr=SR, target=-14.0):
    """Bring a mix to the target loudness through the limiter; returns the master and the deepest gain reduction."""
    gain = target - lufs(x, sr)
    for _ in range(8):
        y, g = limiter(x * undb(gain), sr)
        err = target - lufs(y, sr)
        if abs(err) < 0.05:
            break
        gain += err
    return y, -db(g.min())


# ---------------------------------------------------------------- instruments: SFZ written from sample files

def _dyn_rank(tok):
    return int(tok[1:]) if tok[0] == 'v' else DYN.index(tok)


def instrument(folder, mode, release=0.4, octave=1, legato=False):
    """SFZ for a VSCO folder of <name>_<note><oct>_<v1|mf>[_rr2].wav. mode 'sus': the dynamic layers crossfade on
    CC1, the expression curve; 'short': layers on velocity, round robins alternate. VSCO names octaves one lower
    than scientific pitch (A2 sounds at 220 Hz), hence octave=1; the harp is named in scientific pitch (octave=0).
    legato: a note that starts while another is held skips its attack and fades in, so a line connects
    (for melodies; chords would lose their attacks)."""
    d = VSCO / folder
    out = d / f'_studio_{mode}{"_legato" if legato else ""}.sfz'
    zones = {}
    for f in sorted(d.glob('*.wav')):
        toks = f.stem.split('_')
        i, note = next((i, t) for i, t in enumerate(toks) if re.fullmatch(r'[A-G]#?-?\d', t))
        dyn = next((t for t in toks[i + 1:] if re.fullmatch(r'v\d|[pmf]{1,3}', t)), 'v1')
        zones.setdefault(midi(note.lower()) + 12 * octave, {}).setdefault(dyn, []).append(f.name)
    assert zones, f'no samples in {d}: run setup.py'
    keys = sorted(zones)
    lines = []
    for k, key in enumerate(keys):
        lo = keys[k - 1] + (key - keys[k - 1]) // 2 + 1 if k else key - 12
        hi = key + (keys[k + 1] - key) // 2 if k < len(keys) - 1 else key + 12
        dyns = sorted(zones[key], key=_dyn_rank)
        n = len(dyns)
        for j, dyn in enumerate(dyns):
            if mode == 'sus':
                c = [round(127 * i / (n - 1)) for i in range(n)] if n > 1 else [0]
                layer = (f' xfin_locc1={c[j - 1]} xfin_hicc1={c[j]}' if j else '') + \
                        (f' xfout_locc1={c[j]} xfout_hicc1={c[j + 1]}' if j < n - 1 else '')
                env = f' ampeg_attack=0.03 ampeg_release={release} amp_veltrack=30'
            else:
                layer = f' lovel={1 + 127 * j // n} hivel={127 * (j + 1) // n}'
                env = f' loop_mode=one_shot ampeg_release={release} amp_veltrack=60'
            rrs = zones[key][dyn]
            for r, name in enumerate(rrs):
                seq = f' seq_length={len(rrs)} seq_position={r + 1}' if len(rrs) > 1 else ''
                region = f'<region> sample={name} pitch_keycenter={key} lokey={lo} hikey={hi}{layer}{env}{seq}'
                if legato and mode == 'sus':
                    lines += [region + ' trigger=first',
                              region.replace(' ampeg_attack=0.03', ' ampeg_attack=0.09') + ' trigger=legato offset=4000']
                else:
                    lines.append(region)
    out.write_text('\n'.join(lines) + '\n')
    return out


def decent(preset, release=None):
    """SFZ from a Decent Sampler preset (Virtual Playing Orchestra and Pianobook libraries ship in that format):
    each <sample> keeps its key range, root, velocity range, volume and tuning; each <group> its envelope.
    Parsed with regular expressions: some presets repeat an attribute, which Decent Sampler accepts and XML does not."""
    src = Path(preset)
    out = src.with_name(f'_studio_{src.stem}.sfz')

    def num(el, k, default=None):
        v = el.get(k)
        return default if v is None else float(v.replace('dB', ''))

    def gain(v):
        return float(v.replace('dB', '')) if v.endswith('dB') else 20 * np.log10(max(float(v), 1e-6))

    lines, g, env, gdb = [], {}, '', 0.0
    for tag, attrs in re.findall(r'<(group|sample)\b([^>]*)>', src.read_text(encoding='utf-8', errors='replace')):
        a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
        if tag == 'group':
            g, gdb = a, gain(a.get('volume', '0dB'))
            sus = num(g, 'sustain', 1.0)
            env = (f' ampeg_attack={num(g, "attack", 0.005)} ampeg_decay={num(g, "decay", 1.0)}'
                   f' ampeg_sustain={100 * sus if sus <= 1 else sus} ampeg_release={release or num(g, "release", 0.3)}')
            continue
        path = a.get('path').replace('\\', '/')
        assert (src.parent / path).exists(), f'missing sample {path}: run setup.py'
        vel = f' lovel={a.get("loVel")} hivel={a.get("hiVel")}' if a.get('loVel') else \
              f' lovel={g.get("loVel")} hivel={g.get("hiVel")}' if g.get('loVel') else ''
        pos = a.get('seqPosition') or g.get('seqPosition')
        seq = f' seq_length={g.get("seqLength") or a.get("seqLength")} seq_position={pos}' if pos else ''
        loop = ' loop_mode=loop_continuous' if 'loop' in path.lower() else ''
        lines.append(f'<region> sample={path} pitch_keycenter={a.get("rootNote")} lokey={a.get("loNote")} '
                     f'hikey={a.get("hiNote")} tune={round(float(a.get("tuning", 0)) * 100)} '
                     f'volume={gdb + gain(a.get("volume", "0dB")):.1f}{vel}{seq}{loop}{env}')
    assert lines, f'no samples in {src}'
    out.write_text('\n'.join(lines) + '\n')
    return out


def synth(name, wave='sine', **opcodes):
    """An sfizz oscillator as an instrument: sine, saw, square, triangle or noise, shaped by SFZ opcodes
    (ampeg_*, pitcheg_*, fil_type, cutoff…). For sub bass and electronic layers."""
    d = HOME / 'synth'
    d.mkdir(parents=True, exist_ok=True)
    out = d / f'_studio_{name}.sfz'
    out.write_text(f'<region> sample=*{wave} lokey=0 hikey=127 pitch_keycenter=69 '
                   + ' '.join(f'{k}={v}' for k, v in opcodes.items()) + '\n')
    return out


def percussion(folder, pattern, release=1.0, key=60, name=None):
    """SFZ for unpitched hits: files matching pattern, layered on velocity by their dynamic marking (pp…fff)."""
    d = VSCO / folder
    out = d / f'_studio_{name or pattern.replace("*", "")}.sfz'
    groups = {}
    for f in sorted(d.glob(pattern)):
        dyn = next((t for t in f.stem.split('_') if t in DYN or re.fullmatch(r'v\d', t)), 'mf')
        groups.setdefault(dyn, []).append(f.name)
    assert groups, f'no {pattern} in {d}: run setup.py'
    dyns = sorted(groups, key=_dyn_rank)
    lines = []
    for j, dyn in enumerate(dyns):
        for r, f in enumerate(groups[dyn]):
            seq = f' seq_length={len(groups[dyn])} seq_position={r + 1}' if len(groups[dyn]) > 1 else ''
            lines.append(f'<region> sample={f} key={key} pitch_keycenter={key} lovel={1 + 127 * j // len(dyns)} '
                         f'hivel={127 * (j + 1) // len(dyns)} loop_mode=one_shot ampeg_release={release} amp_veltrack=50{seq}')
    out.write_text('\n'.join(lines) + '\n')
    return out


def _f0(path, fmin=40, fmax=400):
    """Strongest spectral peak between fmin and fmax: the pitch of a timpani."""
    x, sr = sf.read(path, always_2d=True)
    x = x.mean(1)[int(0.05 * sr):int(1.0 * sr)]
    s = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    band = (f > fmin) & (f < fmax)
    return f[band][np.argmax(s[band])]


def timpani(folder='Percussion/Timpani', kind='Hit', release=1.5, veltrack=50):
    """Each VSCO timpani is one drum at one pitch: measure it, then map it to the keys around it.
    Hits ring out whatever the note length; rolls (24 s samples) last as long as the note."""
    mode = 'loop_mode=one_shot ' if kind == 'Hit' else ''
    d = VSCO / folder
    out = d / f'_studio_{kind.lower()}.sfz'
    drums = {}
    for f in sorted(d.glob(f'Timpani*_{kind}_*.wav')):
        drums.setdefault(f.stem.split('_')[0], []).append(f)
    assert drums, f'no Timpani*_{kind}_*.wav in {d}: run setup.py'
    pitched = sorted((69 + 12 * np.log2(_f0(fs[0]) / 440), fs) for fs in drums.values())
    lines = []
    for k, (p, fs) in enumerate(pitched):
        key, cents = int(round(p)), round((round(p) - p) * 100)
        lo = (int(round(pitched[k - 1][0])) + key) // 2 + 1 if k else key - 12
        hi = (key + int(round(pitched[k + 1][0]))) // 2 if k < len(pitched) - 1 else key + 12
        groups = {}
        for f in fs:
            groups.setdefault(f.stem.split('_')[2], []).append(f.name)
        dyns = sorted(groups, key=_dyn_rank)
        for j, dyn in enumerate(dyns):
            for r, name in enumerate(groups[dyn]):
                seq = f' seq_length={len(groups[dyn])} seq_position={r + 1}' if len(groups[dyn]) > 1 else ''
                lines.append(f'<region> sample={name} pitch_keycenter={key} tune={cents} lokey={lo} hikey={hi} '
                             f'lovel={1 + 127 * j // len(dyns)} hivel={127 * (j + 1) // len(dyns)} '
                             f'{mode}ampeg_release={release} amp_veltrack={veltrack}{seq}')
    out.write_text('\n'.join(lines) + '\n')
    return out


class VST:
    """A VST3 instrument in place of an SFZ: the plugin, plus a saved state with the instrument already chosen
    (libraries such as BBC Symphony Orchestra Discover hold many instruments in one plugin)."""

    def __init__(self, path, state=None, warmup=12.0):
        self.path, self.state, self.warmup = str(path), state and str(state), warmup


# ---------------------------------------------------------------- parts

class Part:
    """One instrument track: notes and CC1 expression in eighth notes, plus its place in the mix."""

    def __init__(self, name, sound, pan=0.0, gain=0.0, send=0.25, hpf=None, eq=(), comp=None, ensemble=1, fx=()):
        """sound: an SFZ path, a VST, or a function (part, eighth, rng) -> stereo audio at SR. ensemble: play the part that many times, each copy detuned by a few cents,
        with its own timing and a little spread in the stereo field: a solo sample becomes a section. fx: more
        pedalboard plugins, last in the channel (saturation, for one)."""
        self.name, self.sound, self.pan, self.gain, self.send, self.hpf, self.eq, self.comp = \
            name, sound, pan, gain, send, hpf, list(eq), comp
        self.ensemble, self.fx = ensemble, list(fx)
        self.notes, self.curve, self.fader = [], [], []
        self.keyswitch = None                  # MIDI note that selects the articulation in a sample library
        self.key = None                        # untuned percussion: every note plays this key
        self.lyrics = []                       # sung parts: a syllable per note, in order (see words)

    def note(self, t, dur, pitch, vel=90):
        self.notes.append((t, dur, midi(pitch), int(np.clip(vel, 1, 127))))
        return self

    def hit(self, t, vel=100, dur=1):
        """A note for untuned percussion, whose key the instrument decides."""
        return self.note(t, dur, 60, vel)

    def line(self, t, seq, vel=90, octave=0, legato=0.15):
        """seq: [(pitch or None, eighths), ...] played from t. Notes overlap a little for legato; a repeated pitch
        is cut short instead, or its note-off would silence the next one."""
        for k, (p, d) in enumerate(seq):
            if p is not None:
                same = k + 1 < len(seq) and seq[k + 1][0] == p
                self.note(t, d - 0.1 if same else d + legato, midi(p) + 12 * octave, vel)
            t += d
        return t

    def words(self, t, seq, vel=90):
        """Sung parts: seq [(syllable, pitch, eighths), ...] from t, a syllable None is a rest. Returns the eighth
        after the last note."""
        for syl, p, d in seq:
            if syl:
                self.note(t, d, p, vel)
                self.lyrics.append(syl)
            t += d
        return t

    def expr(self, *points):
        """CC1 curve through (eighth, value 0-127) points, linear in between: dynamics for sustained notes."""
        self.curve += points
        return self

    def vol(self, *points):
        """Fader automation through (eighth, dB) points, linear in dB; 0 dB before the first and after the last."""
        self.fader += points
        return self


def _write_midi(part, path, eighth, rng):
    tpe = 240                                                      # ticks per eighth, 480 per quarter
    ev = []
    for t, d, p, v in part.notes:
        j = rng.normal(0, 0.03)                                    # about 6 ms of human timing
        on = max(2, round((t + j) * tpe))                          # ticks 0-1 belong to the keyswitch
        p = part.key if part.key is not None else p
        v = int(np.clip(v + rng.integers(-4, 5), 1, 127))
        ev += [(on, 1, mido.Message('note_on', note=p, velocity=v)),
               (max(on + 1, round((t + j + d) * tpe)), 0, mido.Message('note_off', note=p, velocity=0))]
    if part.curve:
        pts = sorted(part.curve)
        ts = np.arange(pts[0][0], pts[-1][0] + 0.25, 0.25)
        for t, v in zip(ts, np.interp(ts, *zip(*pts))):
            ev.append((round(t * tpe), -1, mido.Message('control_change', control=1, value=int(round(v)))))
    if part.keyswitch is not None:
        ev += [(0, -2, mido.Message('note_on', note=part.keyswitch, velocity=100)),
               (1, -2, mido.Message('note_off', note=part.keyswitch, velocity=0))]
    ev.sort(key=lambda e: (e[0], e[1]))
    mf = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mf.tracks.append(tr)
    tr.append(mido.MetaMessage('set_tempo', tempo=round(2 * eighth * 1e6)))
    now = 0
    for tick, _, msg in ev:
        tr.append(msg.copy(time=tick - now))
        now = tick
    mf.save(path)


def _render_vst(part, eighth, tmp, rng):
    """A part through a VST3 instrument hosted by DawDreamer, notes and CC1 from the same MIDI file."""
    import dawdreamer as dd
    mid = Path(tmp) / f'{part.name}.mid'
    _write_midi(part, mid, eighth, rng)
    eng = dd.RenderEngine(SR, 512)
    p = eng.make_plugin_processor(part.name, part.sound.path)
    if part.sound.state:
        p.load_state(part.sound.state)
    eng.load_graph([(p, [])])
    time.sleep(part.sound.warmup)                 # sample players stream their samples in the background
    eng.render(1.0)
    p.load_midi(str(mid), clear_previous=True, beats=False, all_events=True)
    eng.render(max(t + d for t, d, _, _ in part.notes) * eighth + 4)
    return np.ascontiguousarray(eng.get_audio().T, dtype=np.float32)


def _render_part(part, eighth, tmp, rng):
    if isinstance(part.sound, VST):
        return _render_vst(part, eighth, tmp, rng)
    if callable(part.sound):                       # a renderer of its own, such as sung voices: (part, eighth, rng)
        return part.sound(part, eighth, rng)
    k = part.ensemble
    copies = []
    for i in range(k):
        sfz = Path(part.sound)
        if k > 1:                                  # a copy detuned from -8 to +8 cents, through an include wrapper
            cents = round(-8 + 16 * i / (k - 1))
            sfz = sfz.with_name(f'{sfz.stem}_tune{cents:+d}.sfz')
            sfz.write_text(f'<global> tune={cents}\n#include "{Path(part.sound).name}"\n')
        mid, wav = Path(tmp) / f'{part.name}-{i}.mid', Path(tmp) / f'{part.name}-{i}.wav'
        _write_midi(part, mid, eighth, rng)
        subprocess.run([str(_tool('sfizz_render.exe' if os.name == 'nt' else 'sfizz_render')), '--sfz', str(sfz),
                        '--midi', str(mid), '--wav', str(wav), '--samplerate', str(SR), '--polyphony', '256'],
                       check=True, capture_output=True)
        x, sr = sf.read(wav, always_2d=True, dtype='float32')
        assert sr == SR, sr
        copies.append(_pan(x, -0.3 + 0.6 * i / (k - 1)) if k > 1 else x)
    n = max(len(x) for x in copies)
    out = np.zeros((n, 2), np.float32)
    for x in copies:
        out[:len(x)] += x
    return out / np.sqrt(k)


# ---------------------------------------------------------------- mix

def _pan(x, p):
    """Constant-power balance of a stereo stem, -1 left to 1 right."""
    a = (p + 1) * np.pi / 4
    return x * (np.array([np.cos(a), np.sin(a)]) * np.sqrt(2))


def _set(proc, name, value):
    """Set a plugin parameter by its displayed value (bisection on the normalized value)."""
    i = next(i for i in range(proc.get_plugin_parameter_size()) if proc.get_parameter_name(i) == name)
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        proc.set_parameter(i, mid)
        if float(proc.get_parameter_text(i).split()[0]) < value:
            lo = mid
        else:
            hi = mid
    proc.set_parameter(i, (lo + hi) / 2)


def hall(x, **params):
    """Dragonfly Hall, wet only. Defaults: a 30 m scoring stage, 2.4 s decay."""
    import dawdreamer as dd
    eng = dd.RenderEngine(SR, 512)
    src = eng.make_playback_processor('src', np.ascontiguousarray(x.T))
    h = eng.make_plugin_processor('hall', str(_tool('DragonflyHallReverb.vst3')))
    p = {'Dry Level': 0, 'Early Level': 25, 'Late Level': 45, 'Size': 30, 'Width': 100, 'Predelay': 18,
         'Decay': 2.4, 'High Cut': 9000, 'Low Cut': 50}
    p.update(params)
    for k, v in p.items():
        _set(h, k, v)
    eng.load_graph([(src, []), (h, ['src'])])
    eng.render(len(x) / SR)
    y = eng.get_audio().T[:len(x)]
    return np.pad(y, ((0, len(x) - len(y)), (0, 0)))         # the render can come back a sample short


def render(parts, out, eighth, tail=4.0, seed=1, report=True, master_fx=(), glue=(-14, 2), **hall_params):
    """Render every part, mix, master. Writes out (the master) and out-stems/<part>.wav (post-fader, dry).
    master_fx: pedalboard plugins on the mix bus before the glue compressor (threshold dB, ratio) and the limiter;
    a hard glue flattens the contrast between sections."""
    out = Path(out)
    stems_dir = out.with_name(out.stem + '-stems')
    stems_dir.mkdir(parents=True, exist_ok=True)
    parts = [p for p in parts if p.notes]
    names = [p.name for p in parts]
    assert len(set(names)) == len(names), f'two parts share a name: {names}'
    rng = np.random.default_rng(seed)
    with tempfile.TemporaryDirectory() as tmp:
        raw = {p.name: _render_part(p, eighth, tmp, rng) for p in parts}
    n = max(len(x) for x in raw.values()) + int(tail * SR)
    dry, send = np.zeros((n, 2), np.float32), np.zeros((n, 2), np.float32)
    rows = []
    for p in parts:
        x = np.zeros((n, 2), np.float32)
        x[:len(raw[p.name])] = raw[p.name]
        fx = ([pb.HighpassFilter(p.hpf)] if p.hpf else []) + [pb.PeakFilter(f, g, q) for f, g, q in p.eq] + \
             ([pb.Compressor(*p.comp)] if p.comp else []) + p.fx
        y = pb.Pedalboard(fx)(x.T, SR).T if fx else x
        if p.fader:
            ts, ds = zip(*sorted(p.fader))
            y = y * undb(np.interp(np.arange(n) / SR, np.array(ts) * eighth, ds, left=0, right=0))[:, None]
        y = _pan(y * undb(p.gain), p.pan)
        y = y.astype(np.float32)
        sf.write(stems_dir / f'{p.name}.wav', y, SR, subtype='PCM_24')
        dry += y
        send += y * p.send
        on = np.abs(y).max(1) > 1e-4
        rows.append((p.name, 10 * np.log10(np.mean(y[on] ** 2) + 1e-12) if on.any() else -120, db(np.abs(y).max())))
    mix = dry + hall(send, **hall_params)
    bus = pb.Pedalboard(list(master_fx) + [pb.Compressor(threshold_db=glue[0], ratio=glue[1], attack_ms=30,
                                                            release_ms=250)])
    master, gr = loud(bus(mix.T, SR).T.astype(np.float64), SR, -14)
    audible = np.nonzero(np.abs(master).max(1) > undb(-60))[0]       # drop the silent end of the tail
    master = master[:audible[-1] + SR // 2] if len(audible) else master
    sf.write(out, master, SR, subtype='PCM_24')
    if report:
        print(f'{"part":<18}{"rms when playing":>18}{"peak":>8}')
        for name, rms, peak in rows:
            print(f'{name:<18}{rms:>15.1f} dB{peak:>7.1f}')
        print(f'master: {lufs(master, SR):.1f} LUFS, limiter {gr:.1f} dB, {len(master) / SR:.1f} s -> {out}')
    return master


def check():
    t = np.arange(SR * 3) / SR
    sine = np.sin(2 * np.pi * 997 * t)[:, None]
    assert abs(lufs(sine) + 3.01) < 0.05, lufs(sine)                  # BS.1770: 997 Hz at 0 dBFS, mono
    y, _ = loud(np.hstack([sine, sine]) * 0.1, SR, -14)
    assert abs(lufs(y) + 14) < 0.1 and db(true_peak(y)) <= CEILING_DB + 0.1
    with tempfile.TemporaryDirectory() as tmp:
        p = Part('check', synth('check', ampeg_release=0.2)).note(0, 4, 'a4', 100)
        m = render([p], Path(tmp) / 'check.wav', eighth=0.25, report=False)
    assert db(np.abs(m).max()) > -20, 'silent render'                 # a sine at -14 LUFS peaks near -11 dBFS
    print('check ok: loudness meter, limiter, sfizz, hall')


if __name__ == '__main__':
    if '--check' in sys.argv:
        check()
