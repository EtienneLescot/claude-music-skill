---
name: music-studio
description: Compose and produce instrumental music, film and orchestral first, the way a composer works with a virtual orchestra. You write the score as Python (notes, articulations, expression curves, sung syllables, mix), the studio renders it through real sampled instruments and a sung choir from the command line, and you check the result with a spectrum and loudness ear. Free open libraries installed by the skill, or BBC Symphony Orchestra Discover when the user has set it up. Use whenever the user asks to make, compose, orchestrate or iterate on music, a soundtrack, a film or game cue, a theme, a jingle or a trailer track.
---

# Music Studio

**You are the composer, orchestrator and mixer; the studio plays.** Like an agent driving Blender rather than a model that outputs a picture, you write every note, articulation, swell, syllable and fader move as code, and real recordings of instruments perform it. You cannot hear: `listen.py` measures and draws the render for you, and the user listens.

Everything runs from a shell, in any coding agent. `<skill>` is this folder (in Claude Code, `${CLAUDE_SKILL_DIR}`); scores live in `tracks/` of the project. Run Python with:

```bash
uv run --python 3.12 --with-requirements <skill>/requirements.txt python <file>
```

## Sound sources

| Mode | What plays | Setup |
|---|---|---|
| `open` (default) | Sonatina Symphonic Orchestra 4.0, a few VSCO 2 percussion, through sfizz | automatic, no account |
| `discover` | BBC Symphony Orchestra Discover (Spitfire Audio) for strings, brass and percussion: real sections recorded together, one hall. It sounds clearly better. | the user's: a Spitfire account, their app, a 2-minute capture |

`Orchestra()` picks `discover` when it is set up, else `open`; `MUSIC_STUDIO_MODE=open|discover` forces one. The same score renders in both. The choir is sung in both modes by singing-voice models (`sing.py`); harp, flute and the `sub` come from the open sources.

## Setup, once per machine

Ask the user before installing.

```bash
uv run --python 3.12 --with-requirements <skill>/requirements.txt python <skill>/setup.py
```

About 2 GB into `STUDIO_HOME` (default `~/.music-studio`; point it at a large disk if the system disk is short), then a self-check. The choir's vocoder is converted once to ONNX with PyTorch in a throwaway uv environment. Windows is tested, and runs the choir on the GPU. On macOS and Linux, install `sfizz` from the package manager if setup finds no `sfizz_render`, and Dragonfly Reverb from its releases page on macOS.

**Discover, optional.** The user signs up at spitfireaudio.com (free, account and mailing list), installs the Spitfire Audio app and BBC Symphony Orchestra Discover, then runs `setup.py --capture`: eleven plugin windows, about two minutes, each checked. The user does this, not you: the app and the windows are not scriptable, and the captured states hold Spitfire's patch data, which its licence keeps on the user's machine.

## Pipeline

1. **Brief.** Turn the request into a brief: identity (style, mood in three words, tempo, metre, key, duration), timeline (sections with bars and seconds), orchestration (who plays what, in which register and articulation), energy curve (where it builds, breaks, peaks: 60 to 75 % of the length), mix, constraints. Show it in at most eight lines and go on; ask only when a structural choice is open and costly (a fixed duration for a video, room for a voice-over).
2. **Score.** Write `tracks/<slug>.py`: constants for harmony and themes, then the parts, then `orch.render(...)`.
3. **Render** it with the command above.
4. **Listen.** `python <skill>/listen.py tracks/<slug>.wav --bar <seconds> --sections "intro:1-8,theme:9-24,..."`, then open `tracks/<slug>.png`. Fix, at most three passes.
5. **Deliver** the WAV (mastered at -14 LUFS), the stems folder and the score. Say what you measured; never say it sounds great.

## Writing a score

```python
import sys; sys.path.insert(0, '<skill>')
from orchestra import Orchestra

E = 60 / 110 / 3                       # seconds per eighth: 6/8 at dotted quarter = 110
def B(bar): return (bar - 1) * 6       # first eighth of a bar (6 eighths in 6/8, 8 in 4/4)

orch = Orchestra()
hn = orch.part('horns', 'long')
bs = orch.part('basses', 'short')
sop = orch.part('choir', 'sopranos')

hn.line(B(9), [('d4', 3), ('a4', 3), ('a4', 2), ('bb4', 1)], vel=110)   # (pitch, eighths), legato
hn.expr((B(9), 86), (B(10), 110), (B(11) - 0.5, 86))                     # CC1: the phrase swells and falls back
for i, v in enumerate([120, 62, 78, 114, 62, 78]):
    bs.note(B(9) + i, 0.6, 'd2', v)                                       # spiccato gallop, accents on the beats
sop.words(B(9), [('do', 'a4', 3), ('mi', 'a4', 3), ('ne', 'd5', 6)], vel=100)   # (syllable, pitch, eighths)
sop.expr((B(9), 75), (B(10), 115), (B(11) - 0.5, 75))
orch.render('tracks/slug.wav', eighth=E)
```

- Time is in eighth notes; pitches in scientific notation (`c4` is middle C) or MIDI numbers.
- `Part.note(t, dur, pitch, vel)`, `line(t, [(pitch, eighths)], vel, octave)`, `words(t, [(syllable, pitch, eighths)], vel)` for the choir, `hit(t, vel)` for untuned percussion, `expr((t, 0-127), ...)` dynamics of sustained notes and of the choir, `vol((t, dB), ...)` fader automation.
- `orch.part(instrument, articulation, name=None, pan=, gain=, send=, hpf=, eq=[(Hz, dB, Q)], fx=[...])`: levels are calibrated per mode; adjust `gain` in dB from the stem report.
- `orch.render(out, eighth, master_fx=[pedalboard plugins], glue=(threshold, ratio), Decay=seconds)`.

**Instruments** (`python <skill>/orchestra.py` lists them):

| Family | Instrument: articulations |
|---|---|
| Strings | `violins`, `violins 2`: long, short, tremolo · `violas`, `celli`: long, short, tremolo · `basses`: long, short |
| Brass | `horns`, `trumpets`, `trombones`, `bass trombones`, `tuba`: long, short |
| Percussion | `timpani`: hit, roll · `bass drum`, `big drum`, `snare`, `tenor drum`, `anvil`: hit · `cymbals`: hit, swell |
| Choir, sung | `choir`: sopranos, altos, tenors, basses (six singers each) |
| Open only | `harp`: short · `flute`: long · `sub`: long (sine, a floor under the basses) |

## The choir

Each section is six singers synthesised from two singing-voice models, each singer with their own timing, tuning, vibrato and timbre. It sings romaji syllables (`do`, `mi`, `ne`, `ka`, `ra`, `a`, `o`...), one per note, from `words()`; `cannot sing` means a syllable is not in its dictionary.

- **Write it as film choirs are written:** held chords, homophonic, on open vowels and Latin-like syllables (do-mi-ne, mi-se-re, a-ve), behind the brass. A fast melody sung note by note sounds like an organ.
- **Ranges tested in tune:** sopranos f4-d5, altos c#4-f4, tenors d3-a3, basses g2-d3; beyond them, check the result.
- **Cost:** on a GPU a section takes about as long to render as it sings; on a CPU several times longer.

## What makes it sound like a film, not a mockup

Learned from listening tests, in order of effect:

1. **The theme.** A short motif with a strong interval (open fifth, a leap of a sixth), a question ending on the dominant, an answer that climbs to the high point. A stepwise line sounds like library music.
2. **Octaves and open fifths.** Double the theme in octaves across sections (trombones below, horns, trumpets, violins above); give the low strings and low brass roots and fifths. Full triads in the middle register sound like a video game.
3. **Fewer, better parts.** More instruments did not change the colour; consistent sources and writing did. In `discover` mode keep everything from Discover where it can.
4. **A real floor.** Basses, tuba, timpani and bass drum on the downbeats; in `open` mode a `sub` a little under the basses.
5. **Dramatic contrast.** Hold back the first statement, drop the floor before the climax, a stop on the dominant with a roll and a cymbal swell, the climax about 4 LUFS above the theme. A hard bus compressor flattens this: keep `glue` around (-14, 2).
6. **Phrase by phrase.** Every sustained phrase gets an `expr` swell; shorts get accented velocities; legato lines for melodies.

## Reading `listen.py`

| Figure | Meaning | Usual target |
|---|---|---|
| LUFS per section | the contrast the listener feels | climax 3 to 5 above the theme, breakdown 4 to 8 below |
| sub+low % | weight | film and trailer 25 to 45 % |
| high+air % | brightness | orchestral 2 to 10 % |
| width | side over mid | 0.2 to 0.5 |
| parts | each stem's level when playing | melody above accompaniment by 3 to 6 dB, choir 6 to 9 dB under the brass |

The figures check the render, never the taste.

## Licences

The music made is the user's. Sonatina Symphonic Orchestra is CC Sampling Plus, VSCO 2 CE CC0, sfizz BSD-2, Dragonfly and DawDreamer GPL-3, BigVGAN MIT. The choir's voices allow commercial use: Namine Ritsu (Canon) without conditions, Hoshino Hanami ~AI❤dol~ (LotteV) with credit, so tell the user to credit "Hoshino Hanami by LotteV" when they release music with the choir. BBC Symphony Orchestra Discover follows Spitfire's terms: music made with it can be released commercially, royalty free; its sounds and patches cannot be redistributed or used to train AI.
