---
name: music-studio
description: Compose and produce instrumental music, film and orchestral first, the way a composer works with a virtual orchestra. You write the score as Python (notes, articulations, expression curves, mix), the studio renders it through real sampled instruments from the command line, and you check the result with a spectrum and loudness ear. Two sound sources, chosen automatically - free open sample libraries installed by the skill, or BBC Symphony Orchestra Discover when the user has installed it. Use whenever the user asks to make, compose, orchestrate or iterate on music, a soundtrack, a film or game cue, a theme, a jingle or a trailer track.
---

# Music Studio

**You are the composer, orchestrator and mixer; the studio plays.** Like an agent driving Blender rather than a model that outputs a picture, you write every note, articulation, swell and fader move as code, and real recordings of instruments perform it. You cannot hear: `listen.py` measures and draws the render for you, and the user listens.

Everything runs from a shell, in any coding agent. `<skill>` is this folder (in Claude Code, `${CLAUDE_SKILL_DIR}`); scores live in `tracks/` of the project. Run Python with:

```bash
uv run --python 3.12 --with dawdreamer --with pedalboard --with mido --with numpy --with soundfile --with scipy --with matplotlib python <file>
```

## Sound sources

| Mode | What plays | Setup | Sound |
|---|---|---|---|
| `open` (default) | VSCO 2 Community Edition (CC0) and Virtual Playing Orchestra (free) through sfizz | automatic, no account | a good mockup |
| `discover` | BBC Symphony Orchestra Discover (Spitfire Audio): real sections recorded together at Maida Vale, one hall | the user gets it free with a Spitfire account, then a 2-minute capture | clearly better, the one to aim for |

`Orchestra()` picks `discover` when the plugin and its captured states are present, else `open`; `MUSIC_STUDIO_MODE=open|discover` forces one. The same score renders in both. Choirs, harp, flute and the `sub` synth come from the open libraries in both modes (Discover has no choir).

## Setup, once per machine

Ask the user before installing.

```bash
python <skill>/setup.py          # sfizz, Dragonfly Reverb and the open samples (~1.2 GB) into STUDIO_HOME, then a self-check
```

`STUDIO_HOME` defaults to `~/.music-studio`; point it at a large disk if the system disk is short. Windows is tested. On macOS and Linux, install `sfizz` from the package manager if setup finds no `sfizz_render`, and Dragonfly Reverb from its releases page on macOS.

**Discover, optional.** The user signs up at spitfireaudio.com (free, account and mailing list), installs the Spitfire Audio app, installs BBC Symphony Orchestra Discover. Then:

```bash
python <skill>/setup.py --capture      # one plugin window per instrument: choose it, Load, close the window
```

Eleven windows, about two minutes, each checked automatically. The user does this, not you: the app and its windows are not scriptable, and the states hold Spitfire's patch data, which its licence does not allow a project to redistribute, so they stay on the user's machine.

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
from studio import midi

E = 60 / 110 / 3                       # seconds per eighth: 6/8 at dotted quarter = 110
def B(bar): return (bar - 1) * 6       # first eighth of a bar (6 eighths in 6/8, 8 in 4/4)

orch = Orchestra()
hn = orch.part('horns', 'long')
bs = orch.part('basses', 'short')
bd = orch.part('bass drum', 'hit')

hn.line(B(9), [('d4', 3), ('a4', 3), ('a4', 2), ('bb4', 1)], vel=110)   # (pitch, eighths); legato built in
hn.expr((B(9), 86), (B(10), 110), (B(11) - 0.5, 86))                     # CC1: the phrase swells and falls back
for i, v in enumerate([120, 62, 78, 114, 62, 78]):
    bs.note(B(9) + i, 0.6, 'd2', v)                                       # spiccato gallop, accents on the beats
bd.hit(B(9), 124)
orch.render('tracks/slug.wav', eighth=E)
```

- Time is in eighth notes; pitches in scientific notation (`c4` is middle C) or MIDI numbers.
- `Part.note(t, dur, pitch, vel)`, `line(t, [(pitch, eighths)], vel, octave)`, `hit(t, vel)` for untuned percussion, `expr((t, 0-127), ...)` dynamics of sustained notes, `vol((t, dB), ...)` fader automation.
- `orch.part(instrument, articulation, name=None, pan=, gain=, send=, hpf=, eq=, fx=)`; levels are pre-calibrated per mode, add `gain` in dB from the stem report.
- `orch.render(out, eighth, master_fx=[pedalboard plugins], glue=(threshold, ratio), Decay=seconds)`.

**Instruments** (`python <skill>/orchestra.py` lists them with their Discover availability):

| Family | Instrument: articulations |
|---|---|
| Strings | `violins`, `violins 2`: long, short, tremolo · `violas`, `celli`: long, short, tremolo · `basses`: long, short |
| Brass | `horns`, `trumpets`, `trombones`, `bass trombones`, `tuba`: long, short |
| Percussion | `timpani`: hit, roll · `bass drum`, `big drum`, `snare`, `tenor drum`, `anvil`: hit · `cymbals`: hit, swell |
| Open only | `harp`: short · `flute`: long · `choir`, `male choir`: long · `sub`: long (sine) |

## What makes it sound like a film, not a mockup

Learned from listening tests, in order of effect:

1. **The theme.** A short motif with a strong interval (open fifth, a leap of a sixth), a question ending on the dominant, an answer that climbs to the high point. A stepwise line sounds like library music.
2. **Octaves and open fifths.** Double the theme in octaves across sections (trombones below, horns, trumpets, violins above); give the low strings and low brass roots and fifths. Full triads in the middle register sound like a video game.
3. **Fewer, better parts.** More instruments did not change the colour; consistent sources and writing did. In `open` mode the sound is the ceiling; in `discover` mode keep everything from Discover where it can (no extra synth layers, no choir loops next to its hall).
4. **A real floor.** Basses, tuba, timpani and bass drum on the downbeats; in `open` mode a `sub` a little under the basses.
5. **Dramatic contrast.** Hold back the first statement, drop the floor before the climax, a stop on the dominant with a roll and a cymbal swell, the climax about 4 LUFS above the theme. A hard bus compressor flattens this: keep `glue` around (-14, 2).
6. **Phrase by phrase.** Every sustained phrase gets an `expr` swell; shorts get accented velocities; legato lines for melodies.

## Reading `listen.py`

| Figure | Meaning | Usual target |
|---|---|---|
| LUFS per section | the contrast the listener feels | climax 3 to 5 above the theme, breakdown 4 to 8 below |
| sub+low % | weight | film and trailer 25 to 45 % |
| high+air % | brightness | orchestral 3 to 10 % |
| width | side over mid | 0.2 to 0.5 |
| parts | each stem's level when playing | melody above accompaniment by 3 to 6 dB |

The figures check the render, never the taste.

## Licences

The music made is the user's. VSCO 2 CE is CC0, Virtual Playing Orchestra free for any use, sfizz BSD-2, Dragonfly and DawDreamer GPL-3. BBC Symphony Orchestra Discover follows Spitfire's terms: music made with it can be released commercially, royalty free; its sounds and patches cannot be redistributed or used to train AI.
