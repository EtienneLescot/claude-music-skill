# Troubleshooting

## A layer is silent

Run `ear.py` with `--stems`. A stem at -120 dB never played; a stem under -45 dBFS is inaudible in the mix.

- `missing` lists sounds outside the palette. Pick one from `SKILL.md`.
- `steinway` often fails: each note is a 7 to 8 MB WAV. Use `piano`.
- `[webaudio] error: Failed to fetch`: a sample host refused or timed out. Reload the page and render again.

## The score does not evaluate

- Strudel turns every quoted string into a pattern, so template literals and string concatenation do not build a melody. Write each phrase as a `"<...>"` pattern and chain phrases with `arrange([8, a], [8, b])`.
- A signal (`sine`, `saw`, `perlin`) is read once per event. On a sound with one event per bar it stays frozen: give it more events (`s("white*16")`, `.segment(16)`).

## The ear does not start

- `Executable doesn't exist`: Chromium is not installed. Run `uv run --with playwright==1.63.0 python -m playwright install chromium`.
- `page error: ear is not defined`: a CDN import failed. jsDelivr has answered 503 for `@strudel/soundfonts`, which is why the ear loads that file from unpkg. Retry, or check the network.
- `... is outside the current folder`: run `ear.py` from the project root, the folder that holds `tracks/`.

## Performance is slow or times out

- Each take of a 2-minute track takes 15 to 30 s on an RTX 4070 Ti when the GPU is free. Another program using the GPU can make it 10 to 20 times slower, and ACE-Step aborts a take after 600 s.
- `perform.py` keeps going when one take fails. Redo it alone with `--seeds 42 --source 0.5`.
- Check the GPU with `nvidia-smi`; VRAM close to full means something else holds it.

## Disk space

ACE-Step and its models need about 10 GB. Point the caches at a large disk before the first run: `UV_CACHE_DIR` for Python packages, `HF_HOME` for model downloads.

## Self-checks

```bash
uv run --project "$ACESTEP_DIR" python perform.py --check
```

checks the loudness meter against BS.1770 reference signals, the dynamics transfer and the limiter ceiling.
