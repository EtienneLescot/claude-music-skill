---
name: music-studio
description: Compose and produce instrumental music, film and orchestral first, electronic too, as a professional composer working with a virtual orchestra and a synthesizer. You follow a composer's method (brief, reference styles, motif first, harmony, form, orchestration, critique), write the score as Python (notes, articulations, synth patches, filter sweeps, sidechain, expression curves, sung syllables, mix), the studio renders it through real sampled instruments, Surge XT and DSP synthesis, and a sung choir from the command line, and you judge the result with a spectrum and loudness ear. Free open libraries installed by the skill, or BBC Symphony Orchestra Discover when the user has set it up. Use whenever the user asks to make, compose, orchestrate or iterate on music, a soundtrack, an electronic track, a film or game cue, a theme, a jingle or a trailer track.
---

# Music Studio

**You are the composer, orchestrator and mixer; the studio plays.** Like an agent driving Blender rather than a model that outputs a picture, you write every note, articulation, swell, syllable and fader move as code, and real recordings of instruments perform it. You cannot hear: `listen.py` measures and draws the render for you, and the user listens.

Everything runs from a shell, in any coding agent. `<skill>` is this folder (in Claude Code, `${CLAUDE_SKILL_DIR}`); scores live in `tracks/` of the project. Run Python with:

```bash
uv run --python 3.12 --with-requirements <skill>/requirements.txt python <file>
```

## The composer's craft

The craft lives in `references/`. Read what the step needs, when it needs it:

| File | Read it |
|---|---|
| `references/method.md` | first, for every request: the steps, taste, originality |
| `references/styles/<style>.md` | at the brief: the style's tempo, harmony, melody, orchestra, form, devices, pitfalls |
| `references/melody.md` | before writing the hook |
| `references/harmony.md` | when choosing progressions, cadences, modulations |
| `references/orchestration.md` | when assigning parts: ranges, layers, doublings, balance, what sounds real |
| `references/critique.md` | after every render: score checks, render targets, questions for the user |
| `references/culture.md` | when the request names a period, a composer or a genre outside the style sheets |

Styles: `epic-trailer`, `adventure-fantasy`, `heroic`, `emotional-drama`, `wonder-magic`, `dark-suspense`, `swashbuckler`, `waltz-romance`, `march`, `cinematic-pop`, `electronic`. For a short catchy piece meant to be shared, start from `cinematic-pop`. For an electronic cue (a launch film, techno, synthwave, industrial), read `styles/electronic.md` and build it with `surge.py`: Surge XT factory patches for drums, basses, hooks and pads, synthesized ticks, hats, risers and booms, filter sweeps and sidechain pumping. Never answer an electronic brief with strings and horns, and say at the brief that electronic is the studio's least proven sound (the style sheet says where it stands). Rock, pop with a band and jazz need guitars, an acoustic kit or saxophones the studio does not have yet: say so, and offer the closest orchestral or electronic style.

## Sound sources

| Mode | What plays | Setup |
|---|---|---|
| `open` (default) | Sonatina Symphonic Orchestra 4.0, a few VSCO 2 percussion, through sfizz | automatic, no account |
| `discover` | BBC Symphony Orchestra Discover (Spitfire Audio) for strings, brass and percussion: real sections recorded together, one hall. It sounds clearly better. | the user's: a Spitfire account, their app, a 2-minute capture |

`Orchestra()` picks `discover` when it is set up, else `open`; `MUSIC_STUDIO_MODE=open|discover` forces one. The same score renders in both. The choir is sung in both modes by singing-voice models (`sing.py`); piano, harp, flute and the `sub` come from the open sources, and electronic parts from Surge XT (`surge.py`) in both modes.

## Setup, once per machine

Ask the user before installing.

```bash
uv run --python 3.12 --with-requirements <skill>/requirements.txt python <skill>/setup.py
```

About 2 GB into `STUDIO_HOME` (default `~/.music-studio`; point it at a large disk if the system disk is short), then a self-check. The choir's vocoder is converted once to ONNX with PyTorch in a throwaway uv environment. Surge XT comes as its plugin alone (about 50 MB on Windows); its factory patches are fetched one by one, a few KB each, when a score names them. Windows is tested, and runs the choir on the GPU. On macOS and Linux, install `sfizz` from the package manager if setup finds no `sfizz_render`, and Dragonfly Reverb from its releases page on macOS.

**Discover, optional.** The user signs up at spitfireaudio.com (free, account and mailing list), installs the Spitfire Audio app and BBC Symphony Orchestra Discover, then runs `setup.py --capture`: eleven plugin windows, about two minutes, each checked. The user does this, not you: the app and the windows are not scriptable, and the captured states hold Spitfire's patch data, which its licence keeps on the user's machine.

## Pipeline

1. **Brief** (`method.md`, the style sheet): eight lines at most, shown to the user, then go on. Ask only when a structural choice is open and costly.
2. **Motif first** (`melody.md`): write the hook alone, two or three candidates, keep the strongest and say why.
3. **Harmony and form** (`harmony.md`): progression, cadences, modulation, a section table with an energy target per section.
4. **Score** (`orchestration.md`): write `tracks/<slug>.py`, constants for harmony and themes, then the parts, then `orch.render(...)`. Long articulations play one note at a time: give each note of a chord its own part. Before rendering, the orchestra prints every note outside an instrument's range and every chord given to a one-note part: fix them all.
5. **Render** it with the command above.
6. **Judge** (`critique.md`): `python <skill>/listen.py tracks/<slug>.wav --bar <seconds> --sections "intro:1-8,theme:9-24,..."`, open `tracks/<slug>.png`, go through the checks. Give `listen.py` several files to read them against the same sections: the previous version, or a reference the user shares (`ffmpeg -i in.mp4 -vn ref.wav` for a video). One change per pass, at most three passes.
7. **Deliver** the WAV (mastered at -14 LUFS), the stems folder and the score, with what you measured and what you would try next. Present real alternatives side by side at equal loudness. Never say it sounds great: the user's ear decides.

## Writing a score

```python
import sys; sys.path.insert(0, '<skill>')
from orchestra import Orchestra
from theory import roman, stack, above

E = 60 / 104 / 2                       # seconds per eighth: 4/4 at 104
def B(bar): return (bar - 1) * 8       # first eighth of a bar (8 eighths in 4/4, 6 in 6/8)

orch = Orchestra()
hn = orch.part('horns', 'long')
vc = orch.part('celli', 'short')
sop = orch.part('choir', 'sopranos')

PROG = roman('I V vi IV', 'D')                                           # ['D', 'A', 'Bm', 'G']
hn.line(B(1), [('a3', 3), ('d4', 1), ('d4', 2), ('e4', 2)], vel=104)     # (pitch, eighths), legato
hn.expr((B(1), 84), (B(2), 112), (B(3) - 0.5, 84))                       # CC1: the phrase swells and falls back
for bar, chord in enumerate(PROG, 1):
    for i, v in enumerate([112, 68, 78, 106, 70, 80, 102, 74]):          # 3+3+2 accents
        vc.note(B(bar) + i, 0.6, above(chord, 'c2'), v)                  # the chord's root at or above c2
    sop.words(B(bar), [('a', above(chord, 'f4'), 7.5)], vel=90)         # (syllable, pitch, eighths)
orch.render('tracks/slug.wav', eighth=E)
```

- Time is in eighth notes; pitches in scientific notation (`c4` is middle C) or MIDI numbers.
- `Part.note(t, dur, pitch, vel)`, `line(t, [(pitch, eighths)], vel, octave)`, `words(t, [(syllable, pitch, eighths)], vel)` for the choir, `hit(t, vel)` for untuned percussion, `expr((t, 0-127), ...)` dynamics of sustained notes and of the choir, `vol((t, dB), ...)` fader automation.
- `theory.roman(numerals, key)` gives chord symbols; `stack(chord, lo)` the chord in root position; `above(chord, lo, tone)` one chord tone (0 root, 1 third, 2 fifth) at or above a pitch; `transpose(chord, semitones)`.
- `orch.part(instrument, articulation, name=None, pan=, gain=, send=, hpf=, eq=[(Hz, dB, Q)], fx=[...])`: levels are calibrated per mode; adjust `gain` in dB from the stem report.
- `orch.render(out, eighth, master_fx=[pedalboard plugins], glue=(threshold, ratio), Decay=seconds)`.

**Instruments** (`python <skill>/orchestra.py` lists them; ranges in `orchestration.md`):

| Family | Instrument: articulations |
|---|---|
| Strings | `violins`, `violins 2`: long, short, tremolo · `violas`, `celli`: long, short, tremolo · `basses`: long, short |
| Brass | `horns`, `trumpets`, `trombones`, `bass trombones`, `tuba`: long, short |
| Percussion | `timpani`: hit, roll · `bass drum`, `big drum`, `snare`, `tenor drum`, `anvil`: hit · `cymbals`: hit, swell |
| Choir, sung | `choir`: sopranos, altos, tenors, basses (six singers each) |
| Open only | `piano`: short · `harp`: short · `flute`: long · `sub`: long (sine, a floor under the basses) |
| Electronic (`surge.py`) | `surge('Category/Patch')`: Surge XT kicks, snares, toms, basses, plucks, leads, pads (`python <skill>/surge.py list Basses`) · `synth(tick \| shaker \| hat \| riser \| boom \| swell)` · `chain(sound, kicks=[kick])`: `part.sweep = True` makes its `expr` curve a ladder low-pass (`cut(hz)`), `part.duck = dB` pumps it on the kicks. These are `Part`s made outside `orch.part`: add them to `orch.parts` |

**The choir** sings romaji syllables (`do`, `mi`, `ne`, `ka`, `ra`, `a`, `o`...), one per note, from `words()`. Write it as film choirs are written: held chords on open vowels and Latin-like syllables, behind the brass. On a GPU a section takes about as long to render as it sings; on a CPU several times longer.

## Licences

The music made is the user's. Sonatina Symphonic Orchestra is CC Sampling Plus (Splendid Grand Piano is Public Domain), VSCO 2 CE CC0, sfizz BSD-2, Surge XT, Dragonfly and DawDreamer GPL-3, BigVGAN MIT. The choir's voices allow commercial use: Namine Ritsu (Canon) without conditions, Hoshino Hanami ~AI❤dol~ (LotteV) with credit, so tell the user to credit "Hoshino Hanami by LotteV" when they release music with the choir. BBC Symphony Orchestra Discover follows Spitfire's terms: music made with it can be released commercially, royalty free; its sounds and patches cannot be redistributed or used to train AI.
