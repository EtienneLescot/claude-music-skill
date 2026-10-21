"""The ear from a shell: render a Strudel score offline in headless Chromium, write its report and spectrogram.

    uv run --with playwright==1.63.0 python -m playwright install chromium         (once)
    uv run --with playwright==1.63.0 python ear.py tracks/slug.strudel [--cycles N] [--section N] [--stems] [--no-save]
    uv run --with playwright==1.63.0 python ear.py --compare tracks/a.wav tracks/b.wav --bpm 110 [--section 1]

Run it from the project root (the folder that holds tracks/). For a score it writes, next to the score:
<slug>.ear.txt (the report it also prints), <slug>.ear.json, <slug>.ear.png (the spectrogram) and <slug>.wav
(the draft, unless --no-save). --compare writes <first>.compare.txt and <first>.compare.png.
"""
import argparse
import json
import sys
import threading
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).parent))
from playwright.sync_api import sync_playwright  # noqa: E402
from serve import make_server  # noqa: E402

TIMEOUT_MS = 20 * 60 * 1000  # a long track with stems takes minutes


def served(path):
    """URL path of a file under the project root, which the server serves."""
    try:
        return '/' + Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        sys.exit(f'{path} is outside the current folder: run ear.py from the project root.')


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # the report quotes the score header; Windows consoles default to cp1252
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('files', nargs='+', help='a .strudel score, or the .wav files to compare')
    p.add_argument('--cycles', type=int)
    p.add_argument('--section', type=int)
    p.add_argument('--stems', action='store_true', help='also render each $: layer alone')
    p.add_argument('--no-save', action='store_true', help='do not write the draft WAV')
    p.add_argument('--compare', action='store_true', help='compare WAV files against the first one')
    p.add_argument('--bpm', type=float, help='tempo, for --compare')
    a = p.parse_args()

    server = make_server(0)  # any free port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    page_url = f'http://127.0.0.1:{server.server_address[1]}/ear.html?'

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        page = browser.new_page(viewport={'width': 1700, 'height': 1000})
        page.on('pageerror', lambda e: print(f'page error: {e}', file=sys.stderr))

        if a.compare:
            if not a.bpm:
                p.error('--compare needs --bpm')
            q = {'compare': ','.join(served(f) for f in a.files), 'bpm': a.bpm, 'section': a.section or 1}
            page.goto(page_url + urlencode(q))
            page.wait_for_function('window.ear && window.ear.result', timeout=TIMEOUT_MS)
            text = '\n\n'.join(f'== {f}\n{t}' for f, t in zip(a.files, page.locator('#compare pre').all_inner_texts()))
            out = Path(a.files[0]).with_suffix('')
            Path(f'{out}.compare.txt').write_text(text, encoding='utf-8')
            page.locator('#compare').screenshot(path=f'{out}.compare.png')
            print(text)
            print(f'\nwrote {out}.compare.txt, {out}.compare.png')
            return

        score = Path(a.files[0])
        q = {'file': served(score)}
        q.update({k: v for k, v in (('cycles', a.cycles), ('section', a.section)) if v})
        if a.stems:
            q['stems'] = 1
        page.goto(page_url + urlencode(q))
        page.wait_for_function('window.ear && window.ear.result', timeout=TIMEOUT_MS)
        result = page.evaluate('ear.result')
        text = page.inner_text('#out')
        out = score.with_suffix('')
        Path(f'{out}.ear.txt').write_text(text, encoding='utf-8')
        Path(f'{out}.ear.json').write_text(json.dumps(result, indent=1), encoding='utf-8')
        page.locator('#spec').screenshot(path=f'{out}.ear.png')
        written = [f'{out}.ear.txt', f'{out}.ear.json', f'{out}.ear.png']
        if result.get('ok') and not a.no_save:
            page.evaluate('path => ear.save(path)', served(f'{out}.wav'))
            written.append(f'{out}.wav')
        print(text)
        print(f'\nshare: {result.get("share")}')
        print('wrote ' + ', '.join(written))
        browser.close()
        sys.exit(0 if result.get('ok') else 1)


if __name__ == '__main__':
    main()
