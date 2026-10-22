# Install

## The skill

Copy `skills/music-studio` into your agent's skills folder, or install the Claude Code plugin (see the README). Then, once, with [uv](https://docs.astral.sh/uv/):

```bash
uv run --python 3.12 --with dawdreamer --with pedalboard --with mido --with numpy --with soundfile --with scipy \
    python skills/music-studio/setup.py
```

It downloads, into `STUDIO_HOME` (default `~/.music-studio`; set it to a large disk if the system disk is short):

| What | From | Licence | Size |
|---|---|---|---|
| sfizz (`sfizz_render`) | GitHub release | BSD-2 | 8 MB |
| Dragonfly Reverb | GitHub release | GPL-3 | 40 MB |
| VSCO 2 Community Edition, the instruments the orchestra uses | GitHub | CC0 | 960 MB |
| Virtual Playing Orchestra choirs and basses | GitHub | free for any use | 100 MB |

Files already present are kept, so it can be re-run. It ends with a self-check (loudness meter, limiter, sfizz, hall). `--check` runs the self-check alone.

| System | Notes |
|---|---|
| Windows | tested |
| Linux | sfizz's release has no binary for Linux: install `sfizz` from your package manager (it provides `sfizz_render`) |
| macOS | install `sfizz` (Homebrew or its release); Dragonfly ships as a `.dmg`: install it, then place or link `DragonflyHallReverb.vst3` in `STUDIO_HOME/tools` |

## BBC Symphony Orchestra Discover (optional, recommended)

The user does these steps; the agent cannot (account, captcha, administrator app).

1. Sign in or create an account at [spitfireaudio.com](https://www.spitfireaudio.com), open the [Discover page](https://www.spitfireaudio.com/products/bbc-symphony-orchestra-discover), click "Sign up to access", accept the mailing list and pass the captcha in your usual browser (embedded browsers often fail it). The order shows at €0.
2. Install the [Spitfire Audio app](https://www.spitfireaudio.com/pages/product-hub) (it asks for administrator rights), sign in, install BBC Symphony Orchestra Discover (240 MB, any drive).
3. Capture the instruments:

   ```bash
   uv run ... python skills/music-studio/setup.py --capture
   ```

   One plugin window per instrument: open the preset list, choose the instrument named in the terminal, click Load, close the window. Eleven windows, about two minutes; each state is checked and asked again if it holds the wrong instrument. The states stay in `STUDIO_HOME/discover`: Spitfire's licence does not allow sharing them.

The orchestra then uses Discover automatically. `MUSIC_STUDIO_MODE=open` forces the open libraries; `BBCSO_VST3` points to the plugin if it is not in the default VST3 folder.
