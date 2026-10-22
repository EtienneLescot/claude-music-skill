"""Install the studio into STUDIO_HOME (default ~/.music-studio): no account, no installer, nothing system-wide.

    uv run --python 3.12 --with dawdreamer --with pedalboard --with mido --with numpy --with soundfile --with scipy \
        python setup.py              # tools and samples, about 1.2 GB, then a self-check
    ... python setup.py --check      # self-check only
    ... python setup.py --capture violins1 horns ...   # Discover: save instrument states on this machine

Downloads: sfizz (BSD-2) and Dragonfly Reverb (GPL-3) from their GitHub releases; the instruments the orchestra uses
from VSCO 2 Community Edition (CC0) and Virtual Playing Orchestra (free for any use). Files already there are kept.
BBC Symphony Orchestra Discover is never downloaded here: it comes from Spitfire Audio, with an account."""
import json
import os
import platform
import sys
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio import HOME, TOOLS, VPO, VSCO  # noqa: E402

VSCO_REPO, VPO_REPO = 'sgossner/VSCO-2-CE', 'eodowd/VirtualPlayingOrchestra'
VSCO_FOLDERS = [
    'Strings/Violin Section/susVib', 'Strings/Violin Section/Spic', 'Strings/Violin Section/Trem',
    'Strings/Viola Section/susvib', 'Strings/Viola Section/spic', 'Strings/Viola Section/trem',
    'Strings/Cello Section/susvib', 'Strings/Cello Section/spic', 'Strings/Cello Section/trem',
    'Strings/Harp', 'Woodwinds/Flute/susvib',
    'Brass/F Horn/sus', 'Brass/F Horn/stac', 'Brass/Trumpet/sus', 'Brass/Trumpet/stac',
    'Brass/Tenor Trombone/sus', 'Brass/Tenor Trombone/stac', 'Brass/Tuba/sus', 'Brass/Tuba/stac',
    'Percussion/Timpani', 'Percussion/Timpani/Rolls', 'VSCO 1 Percussion/drums/bass',
    'VSCO 1 Percussion/drums/snare/drum1', 'VSCO 1 Percussion/drums/tenor/tenor_higher',
    'VSCO 1 Percussion/drums/other/ethnic/giant/sticks', 'VSCO 1 Percussion/varMetal/Cymbals/clash',
    'VSCO 1 Percussion/varMetal/Cymbals/susp', 'VSCO 1 Percussion/varMetal/various',
]
VPO_PRESETS = ['choir-MIXED-sustain', 'choir-MALE-normal-mod-wheel', 'bass-SEC-staccato', 'bass-SEC-sustain']
SYSTEM = {'Windows': ['win64'], 'Darwin': ['macos'], 'Linux': ['linux-x86_64']}[platform.system()]


def get(url, dest=None):
    req = urllib.request.Request(url, headers={'User-Agent': 'music-studio-setup'})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if dest:
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        Path(dest).write_bytes(data)
    return data


def tree(repo):
    branch = json.loads(get(f'https://api.github.com/repos/{repo}'))['default_branch']
    t = json.loads(get(f'https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1'))
    return branch, [x for x in t['tree'] if x['type'] == 'blob']


def fetch_all(jobs):
    """Download (url, dest, size) jobs in parallel, skipping files already complete."""
    todo = [(u, d) for u, d, s in jobs if not (d.exists() and d.stat().st_size == s)]
    print(f'  {len(jobs) - len(todo)} already there, {len(todo)} to download')
    with ThreadPoolExecutor(16) as pool:
        list(pool.map(lambda j: get(*j), todo))


def samples():
    branch, files = tree(VSCO_REPO)
    keep = set(VSCO_FOLDERS)
    jobs = [(f'https://raw.githubusercontent.com/{VSCO_REPO}/{branch}/{urllib.parse.quote(f["path"])}', VSCO / f['path'], f['size'])
            for f in files if f['path'].lower().endswith('.wav') and f['path'].rsplit('/', 1)[0] in keep]
    print(f'VSCO 2 CE: {len(jobs)} samples, {sum(j[2] for j in jobs) / 1e6:.0f} MB')
    fetch_all(jobs)
    branch, files = tree(VPO_REPO)
    jobs = [(f'https://raw.githubusercontent.com/{VPO_REPO}/{branch}/{urllib.parse.quote(f["path"])}', VPO / f['path'], f['size'])
            for f in files if f['path'].endswith('.dspreset') and Path(f['path']).stem in VPO_PRESETS
            or f['path'].lower().endswith('.wav') and f['path'].split('/')[1:2] and f['path'].split('/')[1] in VPO_PRESETS]
    print(f'Virtual Playing Orchestra: {len(jobs)} files, {sum(j[2] for j in jobs) / 1e6:.0f} MB')
    fetch_all(jobs)


def release_asset(repo, must):
    """The latest release asset of a repo that matches this system and contains every word in must."""
    rel = json.loads(get(f'https://api.github.com/repos/{repo}/releases/latest'))
    for a in rel['assets']:
        n = a['name'].lower()
        if any(s in n for s in SYSTEM) and all(m in n for m in must) and n.endswith(('.zip', '.tar.gz', '.tar.xz')):
            return a['browser_download_url'], a['name']
    return None, None


def tools():
    for repo, must, target, hint in (
            ('sfztools/sfizz', [], 'sfizz_render', 'install sfizz with your package manager (it provides sfizz_render)'),
            ('michaelwillis/dragonfly-reverb', [], 'DragonflyHallReverb.vst3', 'download Dragonfly Reverb for your system')):
        if list(TOOLS.rglob(target + ('.exe' if target == 'sfizz_render' and os.name == 'nt' else ''))):
            print(f'{target}: already there')
            continue
        url, name = release_asset(repo, must)
        if not url:
            print(f'{target}: no release for this system; {hint}')
            continue
        archive = TOOLS / name
        print(f'{target}: downloading {name}')
        get(url, archive)
        if name.endswith('.zip'):
            zipfile.ZipFile(archive).extractall(TOOLS / Path(name).stem)
        else:
            import tarfile
            tarfile.open(archive).extractall(TOOLS / name.rsplit('.tar', 1)[0])
        archive.unlink()
        if not list(TOOLS.rglob(target + ('.exe' if target == 'sfizz_render' and os.name == 'nt' else ''))):
            print(f'{target}: not in {name}; {hint}')


# Discover instruments the orchestra uses: state name -> the name the plugin shows in its preset list
DISCOVER = {'violins1': 'Violins 1', 'violins2': 'Violins 2', 'violas': 'Violas', 'celli': 'Celli', 'basses': 'Basses',
            'horns': 'Horns a4', 'trumpets': 'Trumpets a3', 'trombones': 'Tenor Trombones a3',
            'basstrombones': 'Bass Trombones a2', 'tuba': 'Tuba', 'percussion': 'Percussion'}


def state_instrument(path):
    """The instrument a saved Discover state holds. The state is JUCE's VST3 XML; its IComponent is JUCE base64,
    holding Spitfire's own XML whose META tag names the preset."""
    import re
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


def capture(names):
    """Discover: one plugin window per instrument. Choose the instrument named on screen, click Load, close the
    window; the state goes to STUDIO_HOME/discover/<name>.state and is checked. States stay on this machine: they
    hold Spitfire's patch data, which its licence does not let a project redistribute."""
    import dawdreamer as dd
    from orchestra import discover_plugin
    plugin = discover_plugin()
    if not plugin:
        sys.exit('BBC Symphony Orchestra Discover is not installed')
    (HOME / 'discover').mkdir(parents=True, exist_ok=True)
    for name in names or DISCOVER:
        want = DISCOVER[name]
        while True:
            eng = dd.RenderEngine(48000, 512)
            p = eng.make_plugin_processor('bbc', str(plugin))
            print(f'{name}: in the window, open the preset list, choose "{want}", click Load, close the window')
            p.open_editor()
            dest = HOME / 'discover' / f'{name}.state'
            p.save_state(str(dest))
            got = state_instrument(dest)
            if got == want:
                print(f'  saved {name} ({got})')
                break
            print(f'  that window held "{got}", not "{want}": once more')


def report():
    from orchestra import STATES, discover_plugin
    plugin = discover_plugin()
    states = sorted({p.stem for d in STATES if d.exists() for p in d.glob('*.state')})
    print(f'BBC Symphony Orchestra Discover: {"installed" if plugin else "not installed"}; states: {states or "none"}')
    if not plugin:
        print('  optional: get it free at spitfireaudio.com (account), install it with the Spitfire Audio app, '
              'and the orchestra switches to it')


if __name__ == '__main__':
    if '--capture' in sys.argv:
        capture(sys.argv[sys.argv.index('--capture') + 1:])
        sys.exit()
    print(f'STUDIO_HOME = {HOME}')
    if '--check' not in sys.argv:
        tools()
        samples()
    from studio import check
    check()
    report()
