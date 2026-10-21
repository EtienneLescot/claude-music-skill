"""Perform a Strudel draft with ACE-Step 1.5 (local), then finish each take: draft dynamics restored, limiter to -14 LUFS.

    uv run --project "$ACESTEP_DIR" python perform.py tracks/slug.wav [--caption "..." --bpm 110 --key "A minor"]
        [--seeds 42 7 123 777] [--strength 0.9] [--lufs -14] [--out DIR]
    Caption, bpm and key default to the @caption, @bpm and @key header tags of tracks/slug.strudel.
    uv run --project "$ACESTEP_DIR" python perform.py --finish draft.wav take.wav --bpm 110   (no GPU: finishing only)
    uv run --project "$ACESTEP_DIR" python perform.py --check                                  (self-check, no GPU)

Writes DIR/<draft>-s<seed>.wav (finished) and DIR/raw/ (ACE-Step output). ACESTEP_DIR is the ACE-Step 1.5 checkout.
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
from numpy.lib.stride_tricks import sliding_window_view
from scipy import signal

CEILING_DB = -1.0


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def undb(d):
    return 10 ** (np.asarray(d) / 20)


# ---------------------------------------------------------------- loudness (ITU-R BS.1770) and limiter

def kweight_sos(sr):
    K = np.tan(np.pi * 1681.974450955533 / sr)  # stage 1: +4 dB high shelf
    Q, Vh = 0.7071752369554196, 10 ** (3.999843853973347 / 20)
    Vb = Vh ** 0.4996667741545416
    a0 = 1 + K / Q + K * K
    shelf = [(Vh + Vb * K / Q + K * K) / a0, 2 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0,
             1, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]
    K = np.tan(np.pi * 38.13547087602444 / sr)  # stage 2: RLB high-pass
    Q = 0.5003270373238773
    a0 = 1 + K / Q + K * K
    return np.array([shelf, [1, -2, 1, 1, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]])


def lufs(x, sr):
    """Integrated loudness: K-weighting, 400 ms blocks at 75 % overlap, absolute and relative gates."""
    y = signal.sosfilt(kweight_sos(sr), x.reshape(len(x), -1), axis=0)
    blk, hop = round(0.4 * sr), round(0.1 * sr)
    cs = np.vstack([np.zeros((1, y.shape[1])), np.cumsum(y ** 2, axis=0)])
    st = np.arange(1 + (len(y) - blk) // hop) * hop
    z = ((cs[st + blk] - cs[st]) / blk).sum(1)
    z = z[-0.691 + 10 * np.log10(z + 1e-20) > -70]
    rel = -0.691 + 10 * np.log10(z.mean()) - 10
    return -0.691 + 10 * np.log10(z[-0.691 + 10 * np.log10(z) > rel].mean())


def true_peak(x, os=4):
    return np.abs(signal.resample_poly(x, os, 1, axis=0)).max()


def limiter(x, sr, ceiling_db=CEILING_DB, look_ms=2.0, release_db_s=25.0, os=4):
    """Look-ahead limiter on 4x-oversampled peaks; the gain reaches its target exactly at the peak."""
    n = len(x)
    xo = np.abs(signal.resample_poly(x, os, 1, axis=0)).max(1)[:n * os]
    tp = np.maximum(np.pad(xo, (0, n * os - len(xo))).reshape(n, os).max(1), np.abs(x).max(1))
    g = np.minimum(1.0, undb(ceiling_db) / np.maximum(tp, 1e-9))
    L = int(look_ms * sr / 1000)
    g = sliding_window_view(np.r_[g, np.ones(L - 1)], L).min(1)
    k = np.arange(n) * (release_db_s / sr)
    g = undb(np.minimum(np.minimum.accumulate(db(g) - k) + k, 0))
    c = np.cumsum(np.r_[np.ones(L), g])
    g = (c[L:] - c[:-L]) / L
    return x * g[:, None], g


def loud(x, sr, target):
    gain = target - lufs(x, sr)
    for _ in range(8):
        y, g = limiter(x * undb(gain), sr)
        err = target - lufs(y, sr)
        if abs(err) < 0.05:
            break
        gain += err
    return y, -db(g.min())


# ---------------------------------------------------------------- dynamics transfer

def bar_db(x, sr, bar_s):
    """Level of each bar in dB, floored 50 dB under the loudest so silent bars don't skew the average."""
    n, step = int(np.ceil(len(x) / (bar_s * sr))), bar_s * sr
    lv = np.array([10 * np.log10(np.mean(x[int(i * step):int((i + 1) * step)] ** 2) + 1e-12) for i in range(n)])
    return np.maximum(lv, lv.max() - 50)


def match_dynamics(ref, ref_sr, x, sr, bar_s, max_boost=6.0, max_cut=15.0):
    """AI covers keep the timing but flatten the dynamics: give the take the draft's bar-by-bar level curve."""
    a, b = bar_db(ref, ref_sr, bar_s), bar_db(x, sr, bar_s)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    g = np.clip((a - a.mean()) - (b - b.mean()), -max_cut, max_boost)
    gain = np.interp(np.arange(len(x)), (np.arange(n) + 0.5) * bar_s * sr, g)  # linear between bar centres
    return x * undb(gain)[:, None]


def finish(draft_path, take_path, out_path, bpm, target):
    ref, ref_sr = sf.read(draft_path, always_2d=True)
    x, sr = sf.read(take_path, always_2d=True)
    y, gr = loud(match_dynamics(ref, ref_sr, x, sr, 240 / bpm), sr, target)
    sf.write(out_path, y, sr, subtype='PCM_24')
    return lufs(y, sr), db(true_peak(y)), gr


# ---------------------------------------------------------------- ACE-Step

def perform(args):
    root = os.environ.get('ACESTEP_DIR')
    if not root:
        sys.exit('Set ACESTEP_DIR to the ACE-Step 1.5 checkout.')
    sys.path.insert(0, root)
    from acestep.gpu_config import get_gpu_config, set_global_gpu_config
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music
    from acestep.llm_inference import LLMHandler

    draft = Path(args.draft).resolve()
    out = Path(args.out or draft.parent / f'{draft.stem}-takes').resolve()
    (out / 'raw').mkdir(parents=True, exist_ok=True)
    duration = round(sf.info(draft).duration, 2)

    set_global_gpu_config(get_gpu_config())
    dit, llm = AceStepHandler(), LLMHandler()  # the language model is not used by cover
    dit.initialize_service(project_root=root, config_path='acestep-v15-turbo', device='auto')

    for seed in args.seeds:
        t0 = time.time()
        params = GenerationParams(task_type='cover', src_audio=str(draft), caption=args.caption,
                                  audio_cover_strength=args.strength, instrumental=True, lyrics='[Instrumental]',
                                  bpm=args.bpm, keyscale=args.key, timesignature='4', duration=duration,
                                  thinking=False, seed=seed)
        config = GenerationConfig(batch_size=1, use_random_seed=False, seeds=[seed], audio_format='wav')
        result = generate_music(dit, llm, params, config, save_dir=str(out / 'raw' / f's{seed}'))
        if not result.success:
            print(f'seed {seed}: FAILED {result.error}')
            continue
        take = out / f'{draft.stem}-s{seed}.wav'
        level, tp, gr = finish(draft, result.audios[0]['path'], take, args.bpm, args.lufs)
        print(f'seed {seed}: {time.time() - t0:.1f} s, {level:.1f} LUFS, true peak {tp:.1f} dBTP, limiter {gr:.1f} dB -> {take}')


def check():
    sr = 48000
    t = np.arange(sr * 3) / sr
    sine = np.sin(2 * np.pi * 997 * t)[:, None]
    assert abs(lufs(sine, sr) + 3.01) < 0.05, lufs(sine, sr)                       # BS.1770: 997 Hz 0 dBFS mono
    assert abs(lufs(np.hstack([sine, sine]), sr) - 0.0) < 0.05
    bar = 1.0                                                                     # draft: loud, quiet, loud
    ref = np.vstack([sine[:sr] * 0.8, sine[:sr] * 0.1, sine[:sr] * 0.8])
    flat = sine * 0.5                                                             # take: flat
    lv = bar_db(match_dynamics(ref, sr, flat, sr, bar), sr, bar)
    assert lv[0] - lv[1] > 10 and abs(lv[0] - lv[2]) < 1, lv                      # the dip came back
    y, _ = loud(np.hstack([flat, flat]) * 0.3, sr, -14)
    assert abs(lufs(y, sr) + 14) < 0.1 and db(true_peak(y)) <= CEILING_DB + 0.1
    print('check ok')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('draft', nargs='?')
    p.add_argument('take', nargs='?', help='with --finish: an existing take to finish')
    p.add_argument('--caption')
    p.add_argument('--bpm', type=float)
    p.add_argument('--key', default='', help='ACE-Step keyscale, e.g. "A minor" (major or minor only)')
    p.add_argument('--seeds', type=int, nargs='+', default=[42, 7, 123, 777])
    p.add_argument('--strength', type=float, default=0.9)
    p.add_argument('--lufs', type=float, default=-14.0)
    p.add_argument('--out')
    p.add_argument('--finish', action='store_true')
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    if a.check:
        check()
    elif a.finish:
        take = Path(a.take)
        print(finish(a.draft, take, take.with_name(take.stem + '-finished.wav'), a.bpm, a.lufs))
    else:
        if not a.draft:
            p.error('draft required')
        score = Path(a.draft).with_suffix('.strudel')
        tags = dict(re.findall(r'//\s*@(caption|bpm|key)\s+(.+)', score.read_text(encoding='utf-8'))) if score.exists() else {}
        a.caption = a.caption or tags.get('caption', '').strip()
        a.bpm = a.bpm or float(re.match(r'[\d.]*', tags.get('bpm', '')).group() or 0) or None
        a.key = a.key or re.sub(r'\s{2,}.*', '', tags.get('key', '')).strip()  # drop a trailing comment
        if not (a.caption and a.bpm):
            p.error(f'no caption or bpm: pass --caption and --bpm, or add @caption and @bpm to {score}')
        perform(a)
