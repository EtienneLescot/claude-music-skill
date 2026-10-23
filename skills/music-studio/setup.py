"""Install the studio into STUDIO_HOME (default ~/.music-studio): no account, no installer, nothing system-wide.

    uv run --python 3.12 --with-requirements requirements.txt python setup.py   # about 2 GB, then a self-check
    ... python setup.py --check                                                 # self-check only
    ... python setup.py --capture [violins1 horns ...]                          # Discover: save instrument states

Downloads, each from its source, never redistributed: sfizz (BSD-2), Dragonfly Reverb and the Surge XT plugin
(GPL-3) from their GitHub releases (Surge's factory patches come one by one when a score names them, see surge.py);
Sonatina Symphonic Orchestra 4.0 (CC Sampling Plus), only the patches the orchestra plays and the samples they name;
a few percussion samples of VSCO 2 Community Edition (CC0); for the choir, two DiffSinger voices from their authors'
pages (Namine Ritsu by Canon; Hoshino Hanami by LotteV, credit required) and NVIDIA's BigVGAN v2 vocoder (MIT) from
Hugging Face, converted once to ONNX with PyTorch in a throwaway uv environment. Files already there are kept. BBC
Symphony Orchestra Discover is never downloaded here: it comes from Spitfire Audio, with an account."""
import json
import os
import platform
import posixpath
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from fnmatch import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import discover  # noqa: E402
import surge  # noqa: E402
from orchestra import CATALOG, SSO, VSCO, VSCO_FILES  # noqa: E402
from sing import BIGVGAN, VOICEBANKS  # noqa: E402
from studio import HOME, TOOLS, check  # noqa: E402

SSO_REPO, VSCO_REPO = 'peastman/sso', 'sgossner/VSCO-2-CE'
VOICE_URLS = {'ritsu': 'https://www.canon-voice.com/voice/NamineRitsu_DiffSinger.zip',
              'hanami': 'https://www.mediafire.com/file/ks3hpb5zldabo3s/'
                        'Hoshino_Hanami_%257EAIdol%257E_for_DiffSinger_v1.0.zip/file'}
BIGVGAN_URL = 'https://huggingface.co/nvidia/bigvgan_v2_44khz_128band_512x/resolve/main/'
BIGVGAN_FILES = ['LICENSE', 'config.json', 'bigvgan.py', 'activations.py', 'utils.py', 'env.py', 'meldataset.py',
                 'alias_free_activation/torch/__init__.py', 'alias_free_activation/torch/act.py',
                 'alias_free_activation/torch/filter.py', 'alias_free_activation/torch/resample.py',
                 'bigvgan_generator.pt']
SYSTEM = {'Windows': ['win64'], 'Darwin': ['macos'], 'Linux': ['linux-x86_64']}[platform.system()]
SURGE_SYSTEM = {'Windows': 'win64', 'Darwin': 'macos', 'Linux': 'linux'}[platform.system()]


def get(url, dest=None):
    req = urllib.request.Request(url, headers={'User-Agent': 'music-studio-setup'})
    with urllib.request.urlopen(req, timeout=120) as r:
        if not dest:
            return r.read()
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'wb') as f:
            shutil.copyfileobj(r, f, 1 << 20)


def tree(repo):
    """The default branch of a GitHub repo and its files, with their sizes."""
    branch = json.loads(get(f'https://api.github.com/repos/{repo}'))['default_branch']
    t = json.loads(get(f'https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1'))
    return branch, {x['path']: x['size'] for x in t['tree'] if x['type'] == 'blob'}


def raw(repo, branch, path):
    return f'https://raw.githubusercontent.com/{repo}/{branch}/{urllib.parse.quote(path)}'


def fetch_all(jobs):
    """Download (url, dest, size) jobs in parallel, skipping files already complete."""
    todo = [(u, d) for u, d, s in jobs if not (d.exists() and d.stat().st_size == s)]
    print(f'  {len(jobs) - len(todo)} already there, {len(todo)} to download')
    with ThreadPoolExecutor(16) as pool:
        list(pool.map(lambda j: get(*j), todo))


def tools():
    """sfizz_render, Dragonfly Hall and Surge XT from the latest GitHub release built for this system. Surge's stable
    releases live in their own repository (the main one only publishes nightlies); its plugin-only archive is enough."""
    for repo, target, hint, pick in (
            ('sfztools/sfizz', 'sfizz_render', 'install sfizz with your package manager (it provides sfizz_render)',
             lambda n: any(s in n for s in SYSTEM)),
            ('michaelwillis/dragonfly-reverb', 'DragonflyHallReverb.vst3', 'download Dragonfly Reverb for your system',
             lambda n: any(s in n for s in SYSTEM)),
            ('surge-synthesizer/releases-xt', 'Surge XT.vst3', 'install Surge XT from surge-synthesizer.github.io',
             lambda n: n.startswith(f'surge-xt-{SURGE_SYSTEM}-') and 'pluginsonly' in n)):
        exe = target + ('.exe' if target == 'sfizz_render' and os.name == 'nt' else '')
        if list(TOOLS.rglob(exe)) or (target == 'Surge XT.vst3' and surge.plugin()):
            print(f'{target}: already there')
            continue
        rel = json.loads(get(f'https://api.github.com/repos/{repo}/releases/latest'))
        asset = next((a for a in rel['assets'] if pick(a['name'].lower())
                      and a['name'].lower().endswith(('.zip', '.tar.gz', '.tar.xz'))), None)
        if not asset:
            print(f'{target}: no release for this system; {hint}')
            continue
        archive = TOOLS / asset['name']
        print(f'{target}: downloading {asset["name"]}')
        get(asset['browser_download_url'], archive)
        if archive.suffix == '.zip':
            zipfile.ZipFile(archive).extractall(TOOLS / archive.stem)
        else:
            tarfile.open(archive).extractall(TOOLS / archive.name.rsplit('.tar', 1)[0])
        archive.unlink()
        if not list(TOOLS.rglob(exe)):
            print(f'{target}: not in {asset["name"]}; {hint}')


def sonatina():
    """The Sonatina patches the catalog names, their includes, and only the samples they use."""
    branch, size = tree(SSO_REPO)
    root = SSO.name
    samples = set()
    for patch in sorted({e[0] for e in CATALOG.values() if isinstance(e[0], str)}):
        base, todo = posixpath.dirname(patch), [patch]
        while todo:                                    # includes and samples are relative to the patch's folder
            rel = todo.pop()
            if f'{root}/{rel}' not in size:            # an include written with #define macros: see the piano below
                continue
            if not ((SSO / rel).exists() and (SSO / rel).stat().st_size == size[f'{root}/{rel}']):
                get(raw(SSO_REPO, branch, f'{root}/{rel}'), SSO / rel)
            text = (SSO / rel).read_text(encoding='utf-8', errors='replace').replace('\\', '/')   # Windows paths too
            todo += [posixpath.normpath(posixpath.join(base, i)) for i in re.findall(r'#include\s+"([^"]+)"', text)]
            samples |= {posixpath.normpath(posixpath.join(base, m.strip()))
                        for m in re.findall(r'sample=(.+?\.(?:wav|flac|ogg))', text, re.I)}
    # the Grand Piano names its includes and samples through #define macros ($DIR, $EXT): take its folders whole
    samples |= {p[len(root) + 1:] for p in size
                if p.startswith((f'{root}/Grand Piano/', f'{root}/Samples/Grand Piano/'))}
    jobs = [(raw(SSO_REPO, branch, f'{root}/{s}'), SSO / s, size[f'{root}/{s}']) for s in sorted(samples)
            if f'{root}/{s}' in size]
    print(f'Sonatina Symphonic Orchestra: {len(jobs)} samples, {sum(j[2] for j in jobs) / 1e6:.0f} MB')
    fetch_all(jobs)


def vsco():
    """The VSCO 2 percussion Sonatina lacks: only the files the catalog plays."""
    branch, size = tree(VSCO_REPO)
    jobs = [(raw(VSCO_REPO, branch, p), VSCO / p, s) for p, s in size.items()
            if any(posixpath.dirname(p) == d and fnmatch(posixpath.basename(p), f) for d, f in VSCO_FILES)]
    print(f'VSCO 2 CE: {len(jobs)} samples, {sum(j[2] for j in jobs) / 1e6:.0f} MB')
    fetch_all(jobs)


def voices():
    """The choir: two DiffSinger voicebanks from their authors' pages, and BigVGAN v2 converted to ONNX."""
    for name, url in VOICE_URLS.items():
        folder = VOICEBANKS[name]
        if (folder / 'dsconfig.yaml').exists():
            print(f'voice {name}: already there')
            continue
        if 'mediafire.com' in url:                      # the page holds the file's current link
            link = re.search(r'href="(https://download[^"]+)"', get(url).decode('utf-8', 'replace'))
            if not link:
                print(f'voice {name}: download it from {url} and unzip it into {folder.parent}')
                continue
            url = link[1]
        archive = folder.parent / f'{name}.zip'
        print(f'voice {name}: downloading')
        get(url, archive)
        zipfile.ZipFile(archive).extractall(folder.parent)
        archive.unlink()
    if BIGVGAN.exists():
        print('BigVGAN: already there')
        return
    d = BIGVGAN.parent
    print('BigVGAN v2: downloading (490 MB)')
    for f in BIGVGAN_FILES:
        if not (d / f).exists():
            get(BIGVGAN_URL + f, d / f)
    (d / 'alias_free_activation' / '__init__.py').touch()
    uv = shutil.which('uv') or sys.exit('uv not found: it converts BigVGAN to ONNX')
    print('BigVGAN v2: converting to ONNX, once (PyTorch in a throwaway environment)')
    pkgs = [a for m in ('torch', 'onnx', 'huggingface_hub', 'librosa', 'matplotlib', 'tqdm') for a in ('--with', m)]
    subprocess.run([uv, 'run', '--python', '3.12', *pkgs, 'python', '-I',
                    str(Path(__file__).with_name('bigvgan_onnx.py')), str(d)], check=True)
    (d / 'bigvgan_generator.pt').unlink()


def report():
    have = [n for n, f in VOICEBANKS.items() if (f / 'dsconfig.yaml').exists()]
    print(f'choir: voices {have or "none"}, BigVGAN {"ready" if BIGVGAN.exists() else "missing"}')
    discover.report()
    if not discover.plugin():
        print('  optional: BBC Symphony Orchestra Discover is free at spitfireaudio.com (account); once installed '
              'with the Spitfire Audio app, run setup.py --capture and the orchestra switches to it')


if __name__ == '__main__':
    if '--capture' in sys.argv:
        discover.capture(sys.argv[sys.argv.index('--capture') + 1:])
        sys.exit()
    print(f'STUDIO_HOME = {HOME}')
    if '--check' not in sys.argv:
        tools()
        sonatina()
        vsco()
        voices()
    check()
    report()
