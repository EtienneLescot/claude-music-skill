"""The studio's ear: what Claude can check in a render without hearing it.

    uv run --python 3.12 --with-requirements requirements.txt \
        python listen.py tracks/slug.wav --bar 1.636 --sections "intro:1-8,theme:9-24,climax:29-44"

Prints loudness per section (BS.1770, the contrast the listener feels), peak, the energy per band, stereo width and,
when tracks/slug-stems/ exists, each part's level; writes tracks/slug.png, a spectrogram with the sections marked.
--bar is the bar length in seconds (6/8 at dotted quarter 110: 6 * 60 / 110 / 3). The numbers check the render,
never the taste: the listener decides."""
import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio import db, lufs, true_peak  # noqa: E402

BANDS = {'sub <60': (0, 60), 'low <250': (60, 250), 'mid <2k': (250, 2000), 'high <8k': (2000, 8000), 'air': (8000, 24000)}


def bands(x, sr):
    f, p = signal.welch(x.mean(1), sr, nperseg=8192)
    return {k: 100 * p[(f >= lo) & (f < hi)].sum() / p.sum() for k, (lo, hi) in BANDS.items()}


def width(x):
    m, s = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    return float(np.sum(s ** 2) / (np.sum(m ** 2) + 1e-12))


def spectrogram(x, sr, out, sections, bar):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    f, t, z = signal.spectrogram(x.mean(1), sr, nperseg=4096, noverlap=3072)
    fig, ax = plt.subplots(figsize=(14, 5), dpi=100)
    ax.pcolormesh(t, f, 10 * np.log10(z + 1e-12), shading='auto', cmap='magma', vmin=-110, vmax=-30)
    ax.set_yscale('symlog', linthresh=200)
    ax.set_ylim(30, 16000)
    for name, a, _ in sections:
        ax.axvline((a - 1) * bar, color='white', lw=0.8)
        ax.text((a - 1) * bar + 0.3, 12000, name, color='white', fontsize=9)
    ax.set_xlabel('seconds')
    ax.set_ylabel('Hz')
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('wav')
    ap.add_argument('--bar', type=float, help='bar length in seconds')
    ap.add_argument('--sections', default='', help='name:first-last bars, comma separated')
    a = ap.parse_args()
    x, sr = sf.read(a.wav, always_2d=True)
    sections = [(n, int(r.split('-')[0]), int(r.split('-')[1])) for n, r in
                (s.split(':') for s in a.sections.split(',') if s)]
    print(f'{Path(a.wav).name}: {len(x) / sr:.1f} s, {lufs(x, sr):.1f} LUFS, true peak {db(true_peak(x)):.1f} dBTP, '
          f'width {width(x):.2f}')
    print('bands: ' + '  '.join(f'{k} {v:.1f}%' for k, v in bands(x, sr).items()))
    if sections and a.bar:
        print(f'{"section":<12}{"LUFS":>7}{"sub+low %":>11}{"high+air %":>12}')
        for n, first, last in sections:
            y = x[int((first - 1) * a.bar * sr):int(last * a.bar * sr)]
            if len(y) < sr:
                print(f'{n:<12} past the end of the file: check --bar')
                continue
            b = bands(y, sr)
            print(f'{n:<12}{lufs(y, sr):>7.1f}{b["sub <60"] + b["low <250"]:>11.1f}{b["high <8k"] + b["air"]:>12.1f}')
    stems = Path(a.wav).with_name(Path(a.wav).stem + '-stems')
    if stems.exists():
        print('parts (level in the mix, when playing):')
        for f in sorted(stems.glob('*.wav')):
            y, _ = sf.read(f, always_2d=True)
            on = np.abs(y).max(1) > 1e-4
            print(f'  {f.stem:<20}{10 * np.log10(np.mean(y[on] ** 2) + 1e-12) if on.any() else -120:>7.1f} dB')
    png = Path(a.wav).with_suffix('.png')
    spectrogram(x, sr, png, sections, a.bar or 1.0)
    print(f'wrote {png}')


if __name__ == '__main__':
    main()
