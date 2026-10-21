# strudel-composer

A Claude skill: Opus composes music as Strudel code, an offline ear checks the score, and ACE-Step 1.5 performs it on your GPU.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Instructions for Claude: pipeline, composition rules, style captions |
| `ear.html` | Offline Strudel renderer and analyser (spectrogram, metrics, stems, comparison) |
| `serve.py` | Local static server that also accepts `PUT` of `.wav` files |
| `perform.py` | ACE-Step performance, dynamics transfer and limiter to -14 LUFS |

## Requirements

- A browser Claude can drive, for the ear: Claude's built-in browser, Claude in Chrome, or Playwright.
- Python 3.11 or 3.12 and [uv](https://docs.astral.sh/uv/).
- An NVIDIA GPU with at least 4 GB of VRAM (tested on an RTX 4070 Ti, 12 GB), about 10 GB of disk for ACE-Step and its models.
- Network access to jsDelivr and raw.githubusercontent.com (Strudel and its samples load from there).

## Install ACE-Step 1.5

```bash
git clone --depth 1 https://github.com/ace-step/ACE-Step-1.5 /path/to/ACE-Step-1.5
cd /path/to/ACE-Step-1.5
uv sync
```

The models (about 5 GB) download into `checkpoints/` on the first run. If your system disk is short on space, point the caches elsewhere before running anything:

```bash
export UV_CACHE_DIR=/big/disk/uv-cache
export HF_HOME=/big/disk/hf-cache
```

Then tell the skill where ACE-Step lives, and check the finishing chain:

```bash
export ACESTEP_DIR=/path/to/ACE-Step-1.5
uv run --project "$ACESTEP_DIR" python perform.py --check
```

On Windows PowerShell, use `$env:ACESTEP_DIR = 'E:\ACE-Step-1.5'` and the same for the caches.

## Licences

- Strudel is AGPL-3.0. `ear.html` loads it from a CDN and does not redistribute it.
- ACE-Step 1.5 code is MIT. Check the licence of its model weights on Hugging Face before any commercial use.
- Strudel's sample banks (dough-samples, VCSL, tidal-drum-machines) carry their own licences.
