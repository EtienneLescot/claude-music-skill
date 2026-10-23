"""Sung voices: a choir whose singers are DiffSinger voicebanks, the ONNX models OpenUtau uses, read here without
OpenUtau. The score gives each sung note a syllable (Part.words); a section of several singers, each with their own
timing, tuning, vibrato and timbre, sings the line, and BigVGAN v2 turns their spectra into sound.

    sop = orch.part('choir', 'sopranos')
    sop.words(B(29), [('do', 'a4', 3), ('mi', 'a4', 3), ('ne', 'd5', 6)], vel=100)

Voices, downloaded by setup.py into STUDIO_HOME/voices: Hoshino Hanami ~AI*dol~ by LotteV sings the upper sections
(commercial use allowed, credit required), Namine Ritsu by Canon the lower ones (commercial use allowed). The vocoders
shipped with DiffSinger voices are non-commercial (CC BY-NC-SA); NVIDIA's BigVGAN v2 (MIT) replaces them.

The variance models of the voicebanks are not used: the score gives the pitch, the notes give the timing, and
dynamics are a gain plus a blend of the voice's soft and loud timbres. Syllables are romaji (do, mi, ne, ka, ra...)."""
from functools import cache
from pathlib import Path

import numpy as np
import onnxruntime as ort
import yaml
from scipy import signal
from scipy.ndimage import gaussian_filter1d

from studio import HOME, SR

VOICES = HOME / 'voices'
VOICEBANKS = {'hanami': VOICES / 'hanami' / 'Hoshino Hanami ~AIdol~ for DiffSinger v1.0',
              'ritsu': VOICES / 'ritsu' / 'NamineRitsu_DiffSinger'}
BIGVGAN = VOICES / 'bigvgan' / 'bigvgan.onnx'
# section: voicebank, formant shift in semitones (negative is darker)
SECTIONS = {'sopranos': ('hanami', 0.0), 'altos': ('hanami', -3.0), 'tenors': ('ritsu', 0.0), 'basses': ('ritsu', 0.0)}
VSR, HOP = 44100, 512                                  # the frames of DiffSinger and of BigVGAN


def _session(path):
    """An ONNX session on the GPU through DirectML (onnxruntime-directml, Windows) when there is one, else the CPU."""
    opts = ort.SessionOptions()
    opts.log_severity_level = 3
    gpu = [p for p in ('DmlExecutionProvider',) if p in ort.get_available_providers()]
    if gpu:
        opts.enable_mem_pattern = False                    # DirectML's requirements
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    return ort.InferenceSession(str(path), opts, providers=gpu + ['CPUExecutionProvider'])


def _mel_basis(fmin, fmax, n=128, n_fft=2048, sr=VSR):
    """Slaney mel filterbank, as librosa.filters.mel builds it (both DiffSinger and BigVGAN use it)."""
    def mel(f):
        f = np.asarray(f, float)
        return np.where(f < 1000, f * 3 / 200, 15 + np.log(np.maximum(f, 1e-9) / 1000) * 27 / np.log(6.4))

    def hz(m):
        return np.where(m < 15, m * 200 / 3, 1000 * np.exp((m - 15) * np.log(6.4) / 27))

    edges = hz(np.linspace(mel(fmin), mel(fmax), n + 2))
    bins = np.linspace(0, sr / 2, n_fft // 2 + 1)
    up = (bins[None] - edges[:-2, None]) / np.diff(edges)[:-1, None]
    down = (edges[2:, None] - bins[None]) / np.diff(edges)[1:, None]
    return np.maximum(0, np.minimum(up, down)) * (2 / (edges[2:] - edges[:-2]))[:, None]


class BigVGAN:
    """NVIDIA BigVGAN v2, 44 kHz, 128 bands (MIT): a universal vocoder. DiffSinger's mel bands span 40 Hz-16 kHz and
    BigVGAN's the whole spectrum, so each frame goes back to a linear spectrum and onto BigVGAN's bands."""

    def __init__(self, path=BIGVGAN):
        assert Path(path).exists(), f'{path} missing: run setup.py'
        self.session = _session(path)
        self.back, self.to = np.linalg.pinv(_mel_basis(40, 16000)), _mel_basis(0, VSR / 2)

    def __call__(self, mel):
        """mel: [frames, 128], natural log of DiffSinger mel magnitudes -> audio at VSR."""
        lin = np.maximum(self.back @ np.exp(mel).T, 0)
        x = np.log(np.maximum(self.to @ lin, 1e-5)).astype(np.float32)[None]
        return self.session.run(None, {'mel': x})[0][0, 0]


class Voice:
    """One DiffSinger voicebank: acoustic model, speakers and romaji dictionary."""

    def __init__(self, folder, soft=None, loud=None):
        """soft, loud: speakers whose timbres stand for the quiet and the loud end of the dynamics."""
        self.dir = d = Path(folder)
        assert (d / 'dsconfig.yaml').exists(), f'{d} missing: run setup.py'
        self.cfg = cfg = yaml.safe_load((d / 'dsconfig.yaml').read_text(encoding='utf-8'))
        assert (cfg.get('sample_rate', VSR), cfg.get('hop_size', HOP), cfg.get('num_mel_bins', 128),
                cfg.get('mel_fmin', 40), cfg.get('mel_fmax', 16000)) == (VSR, HOP, 128, 40, 16000), 'unusual mels'
        self.tokens = {p: i for i, p in enumerate((d / cfg['phonemes']).read_text(encoding='utf-8').split())}
        self.acoustic = _session(d / cfg['acoustic'])
        self.inputs = {i.name for i in self.acoustic.get_inputs()}
        self.ln = np.log(10) if str(cfg.get('mel_base', '10')) == '10' else 1.0     # to natural log
        self.speakers = {Path(s).name: np.fromfile(d / f'{s}.emb', np.float32) for s in cfg.get('speakers') or []}
        self.soft, self.loud = soft, loud
        self.shift = ((cfg.get('augmentation_args') or {}).get('random_pitch_shifting') or {}).get('range', [-12, 12])
        self.words = {}
        for f in sorted(d.rglob('dsdict*.yaml'), key=lambda f: (f.stem != 'dsdict-ja', f.stem != 'dsdict')):
            for e in (yaml.load(f.read_text('utf-8'), Loader=yaml.BaseLoader) or {}).get('entries') or []:
                self.words.setdefault(e['grapheme'], e['phonemes'])      # BaseLoader: "no" stays a syllable

    def phonemes(self, syllable):
        ph = self.words.get(syllable)
        assert ph and all(p in self.tokens for p in ph), f'{self.dir.name} cannot sing "{syllable}"'
        return ph

    def mel(self, notes, formant=0.0, dyn=None, vibrato=(5.5, 0.2, 0.0), cents=0.0, timbre=None, seed=0, steps=20):
        """notes: [(start s, length s, MIDI pitch, syllable)] from time 0 -> natural-log mel [frames, 128] from 0.
        formant: semitones of formant shift. dyn: seconds -> 0..1, soft to loud timbre. vibrato: (Hz, semitones,
        phase), growing in after a quarter second of each note. timbre: weights of the speakers, None for the first."""
        fr = HOP / VSR
        segs, prev = [('SP', 0.0, 0.0)], 0.0                # (phoneme, start, end)
        for k, (t, d, _, syl) in enumerate(notes):
            ph = self.phonemes(syl)
            cons = ph[:-1]
            cl = min(0.07 * len(cons), (t - prev) / 3 if k else t)   # consonants come before the beat
            start = t - cl
            if start > segs[-1][2] + 1e-3:
                segs.append(('SP', segs[-1][2], start))
            else:
                segs[-1] = (segs[-1][0], segs[-1][1], start)        # legato: the vowel runs into this consonant
            segs += [(c, start + cl * i / len(cons), start + cl * (i + 1) / len(cons)) for i, c in enumerate(cons)]
            segs.append((ph[-1], t, t + d))
            prev = t
        segs = [s for s in segs if s[2] > s[1]] + [('SP', segs[-1][2], segs[-1][2] + 0.3)]
        bounds = np.round(np.array([s[1] for s in segs] + [segs[-1][2]]) / fr).astype(int)
        dur = np.maximum(np.diff(bounds), 1)
        n = int(dur.sum())
        times = np.arange(n) * fr
        idx = np.clip(np.searchsorted(np.array([t for t, *_ in notes]) - 0.07, times, side='right') - 1,
                      0, len(notes) - 1)
        semis = gaussian_filter1d(np.array([notes[i][2] for i in idx], float), 0.04 / fr)   # 40 ms glides
        since = times - np.array([notes[i][0] for i in idx])
        rate, amount, phase = vibrato
        semis += amount * np.clip((since - 0.25) / 0.4, 0, 1) * np.sin(2 * np.pi * rate * np.maximum(since, 0) + phase)
        semis += cents / 100 + gaussian_filter1d(np.random.default_rng(seed).normal(0, 1, n), 0.3 / fr) * 0.6
        feed = {'tokens': np.array([[self.tokens[s[0]] for s in segs]], np.int64),
                'durations': dur[None].astype(np.int64),
                'f0': (440.0 * 2 ** ((semis - 69) / 12)).astype(np.float32)[None]}
        if 'gender' in self.inputs:
            feed['gender'] = np.full((1, n), formant / (self.shift[1] if formant > 0 else -self.shift[0]), np.float32)
        if 'velocity' in self.inputs:
            feed['velocity'] = np.ones((1, n), np.float32)
        if 'spk_embed' in self.inputs:
            names = list(self.speakers)
            w = np.zeros(len(names))
            w[0] = 1
            if timbre is not None:
                w = np.asarray(timbre, float) / np.sum(timbre)
            base = sum(wi * self.speakers[k] for wi, k in zip(w, names))
            soft, loud = self.speakers.get(self.soft, base), self.speakers.get(self.loud, base)
            lv = (np.clip(dyn(times), 0, 1) if dyn else np.full(n, 0.5))[:, None]
            emb = np.where(lv < 0.5, soft + (base - soft) * 2 * lv, base + (loud - base) * (2 * lv - 1))
            feed['spk_embed'] = emb[None].astype(np.float32)
        if self.cfg.get('use_continuous_acceleration'):            # depth 0..1 and a number of steps
            feed['depth'] = np.array(self.cfg.get('max_depth', 1.0), np.float32)
            feed['steps'] = np.array(steps, np.int64)
        else:                                                       # depth out of 1000, every `speedup` steps
            depth = int(self.cfg.get('max_depth', 1000)) if 'depth' in self.inputs else 1000
            speedup = max(1, depth // steps)
            while 'depth' not in self.inputs and 1000 % speedup:
                speedup -= 1
            feed['speedup'] = np.array(speedup, np.int64)
            if 'depth' in self.inputs:
                feed['depth'] = np.array(depth // speedup * speedup, np.int64)
        return self.acoustic.run(None, feed)[0][0] * self.ln


@cache
def voice(name):
    return Voice(VOICEBANKS[name], **({'soft': 'Nectar', 'loud': 'Fragrance'} if name == 'hanami' else {}))


@cache
def vocoder():
    return BigVGAN()


class Choir:
    """A choir section as a Part's sound: each singer sings the part's line with their own timing, tuning,
    vibrato and timbre, panned across `spread`. The part's CC1 curve and velocities are its dynamics."""

    def __init__(self, section, singers=6, spread=0.4):
        self.section, self.singers, self.spread = section, singers, spread

    def __call__(self, part, eighth, rng):
        name, formant = SECTIONS[self.section]
        v = voice(name)
        lyrics = part.lyrics + ['a'] * (len(part.notes) - len(part.lyrics))      # notes without words sing "a"
        notes = sorted(zip(part.notes, lyrics), key=lambda x: x[0][0])
        start = max(0.0, notes[0][0][0] * eighth - 0.5)
        if part.curve:
            ts, vs = zip(*sorted(part.curve))
            cc = lambda t: np.interp(np.asarray(t) / eighth, ts, vs) / 127      # noqa: E731
        else:
            cc = lambda t: np.full(np.shape(t), 0.75)                             # noqa: E731
        out = np.zeros((int((max(t + d for (t, d, _, _), _ in notes) * eighth + 2) * SR), 2), np.float32)
        at = int(start * SR)
        for s in range(self.singers):
            late = rng.normal(0, 0.015)
            sung = [(t * eighth - start + late + rng.normal(0, 0.008), d * eighth, p, syl)
                    for (t, d, p, _), syl in notes]
            mel = v.mel(sung, formant=formant + rng.normal(0, 0.6), dyn=lambda t: cc(t + start),
                        vibrato=(rng.uniform(4.8, 6.0), rng.uniform(0.12, 0.3), rng.uniform(0, 6.3)),
                        cents=rng.normal(0, 7), timbre=rng.dirichlet([3] + [1] * (len(v.speakers) - 1))
                        if len(v.speakers) > 1 else None, seed=int(rng.integers(1 << 30)))
            y = signal.resample_poly(vocoder()(mel), SR // 300, VSR // 300)[:len(out) - at]
            pan = -self.spread + 2 * self.spread * s / max(1, self.singers - 1)
            out[at:at + len(y)] += np.stack([y * np.sqrt(0.5 - pan / 2), y * np.sqrt(0.5 + pan / 2)], 1)
        t = np.arange(len(out)) / SR
        vel = np.interp(t, [n[0] * eighth for n, _ in notes], [n[3] / 127 for n, _ in notes])
        return out * (cc(t) ** 1.5 * vel)[:, None].astype(np.float32) / np.sqrt(self.singers)


if __name__ == '__main__':                         # self-check: the mel basis matches librosa's, when it is there
    try:
        import librosa
        for lo, hi in ((40, 16000), (0, VSR / 2)):
            assert np.allclose(_mel_basis(lo, hi), librosa.filters.mel(sr=VSR, n_fft=2048, n_mels=128, fmin=lo,
                                                                         fmax=hi), atol=1e-6)
        print('mel basis matches librosa')
    except ImportError:
        print('librosa not installed: mel basis not compared')
    y = signal.resample_poly(vocoder()(np.full((100, 128), -4.0)), SR // 300, VSR // 300)
    assert len(y) > 0.9 * SR and np.isfinite(y).all()
    print(f'BigVGAN ok on {ort.get_available_providers()[0]}')
