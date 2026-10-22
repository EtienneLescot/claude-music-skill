# Troubleshooting

## Setup

- **`sfizz_render not found`**: run `setup.py`; on Linux and macOS install `sfizz` from the package manager.
- **`no samples in …: run setup.py`**: a download was interrupted; run `setup.py` again, it only fetches what is missing.
- **GitHub API rate limit** (HTTP 403 during setup): unauthenticated calls are limited to 60 an hour; run setup again later. Sample downloads themselves are not limited.

## Rendering

- **A part is silent**: check its notes fall in the instrument's range (`python orchestra.py` lists the instruments). Discover's timpani sound from MIDI 48; the orchestra shifts them for you.
- **A Discover part is silent or cut at the start**: the plugin streams its samples in the background; raise the warm-up (`VST(..., warmup=20)`) on a slow disk.
- **Two parts share a name**: give one `name=` in `orch.part(...)`.
- **The climax does not stand out**: compare the sections' LUFS in `listen.py`; ease the glue compressor or hold back the earlier section.

## Discover

- **The captcha fails**: do the sign-up in your usual browser, not an embedded one.
- **The Spitfire app does not respond to automation**: it always runs as administrator, and Windows blocks other programs from clicking in it. Do those clicks yourself.
- **`setup.py --capture` asks again**: the window held another instrument than the one named; choose the right one, click Load, close.
- **The plugin window does not close on the first click** after loading: click again, or press Alt+F4 with the window focused.
