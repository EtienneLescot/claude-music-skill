# Troubleshooting

## Setup

- **`sfizz_render not found`**: run `setup.py`; on Linux and macOS install `sfizz` from the package manager.
- **`no samples in …: run setup.py`**: a download was interrupted; run `setup.py` again, it only fetches what is missing.
- **GitHub API rate limit** (HTTP 403 during setup): unauthenticated calls are limited to 60 an hour; run setup again later. Sample downloads themselves are not limited.
- **`voice hanami: download it from …`**: MediaFire changed its page; download the zip from that link by hand and unzip it where the message says.
- **The BigVGAN conversion fails**: it needs `uv` on the PATH and about 1 GB for PyTorch in uv's cache; run setup again.

## Rendering

- **A part is silent**: check its notes fall in the instrument's range (`python orchestra.py` lists the instruments). Long articulations need CC1: the orchestra adds a flat curve when the score draws none.
- **Two parts share a name**: give one `name=` in `orch.part(...)`.
- **The climax does not stand out**: compare the sections' LUFS in `listen.py`; ease the glue compressor or hold back the earlier section.
- **`cannot sing "…"`**: the choir sings romaji syllables (`do`, `mi`, `ka`, `ra`, `a`, `o`…); English words are not in its dictionary.
- **The choir is slow**: without a GPU (or outside Windows) its models run on the CPU, several times slower than real time.

## Discover

- **A Discover part is silent or cut at the start**: the plugin streams its samples in the background; raise the warm-up (`VST(..., warmup=20)` in `discover.py`) on a slow disk. Its timpani sound an octave above the open ones; the orchestra shifts them for you.
- **The captcha fails**: do the sign-up in your usual browser, not an embedded one.
- **The Spitfire app does not respond to automation**: it always runs as administrator, and Windows blocks other programs from clicking in it. Do those clicks yourself.
- **`setup.py --capture` asks again**: the window held another instrument than the one named; choose the right one, click Load, close.
- **The plugin window does not close on the first click** after loading: click again, or press Alt+F4 with the window focused.
