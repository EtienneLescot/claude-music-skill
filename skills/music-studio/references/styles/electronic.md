# Electronic

Sounds like: Gesaffelstein, Moderat, Jon Hopkins, Trent Reznor and Atticus Ross. For launch films, tech and motion design, dark club and industrial trailers.

| | |
|---|---|
| Tempo, metre | 4/4; 105 to 115 BPM for a heavy launch or trailer cue, 120 to 128 for club drive |
| Key, mode | minor (Aeolian) or Dorian; roots on A, E, F or G put the bass in the 40 to 60 Hz pocket under the kick |
| Harmony | static: one chord for two bars or more, a two-chord pendulum (`i v`, `i bVI`, `i bVII`) or a dark loop (`i bVI bIII bVII`); open fifths low, the colour in the hook |
| Melody | a hook of 3 to 5 notes repeated as an ostinato; in dotted eighths it runs 3 against 4 over the grid and turns hypnotic; it enters filtered, opens, and jumps an octave for the last lift |
| Rhythm | a 16th-note pulse from the first bar (ticks, shaker, hats); the kick on every beat for the drive, in half time for a breakdown while the 16ths keep running; a rolling bass on the three 16ths after each kick |
| Sounds | kick, rolling or distorted bass, 16th hats, a pluck or lead hook, a drone or a pad; risers, booms and crashes for transitions; a treated piano or orchestral hits for cinematic colour |
| Form | layers rather than themes: a new element every 2 or 4 bars, a riser and one silent 16th before each drop, a breakdown that keeps the pulse, a final hit or a button |
| Signature devices | a low-pass filter opening across a build; sidechain pumping on the kick; a snare roll accelerating from 8ths to 32nds; a hard stop after the last hit |
| Pitfalls | answering with strings and brass; humanized timing (electronic sits dead on the grid); kick and bass fighting below 100 Hz; a breakdown that drops the pulse; a wall of sub that pushes the limiter past 3 dB |
| In this studio | `surge.py`: Surge XT factory patches for kick, snare, toms, basses, hook, pad and drone; synthesized `tick`, `shaker`, `hat`, `riser`, `boom`, `swell`; `chain` for filter sweeps and sidechain; `piano` short through a tape chain; `anvil`, `big drum`, `timpani`, `cymbals` for hits |

## Where it stands

Tell the user at the brief. The first electronic cue, Launch (a 50 s product film, October 2026), was played by synths written by hand in numpy. Heard next to Suno's take on the same prompt: « La version de Suno est largement meilleure. C'est presque sans comparaison. » Surge XT factory patches then replaced its kick, snare, toms, basses, hook, pad and drone; that version is not judged yet. The hats, ticks, shaker, risers and booms are still synthesized by hand.

## Writing the parts

```python
import sys; sys.path.insert(0, '<skill>')
from orchestra import Orchestra
from studio import Part
from surge import chain, cut, hat, surge, synth

orch = Orchestra()
kick = Part('kick', surge('Percussion/Kick Tech 1'), send=0.02)
bass = Part('bass', chain(surge('Basses/Dist Bass 1'), kicks=[kick]), send=0.0)
hook = Part('hook', chain(surge('Plucks/Saw Pluck'), kicks=[kick]), send=0.15, hpf=120)
hats = Part('hats', synth(hat), pan=0.1, gain=-3, send=0.05)
orch.parts += [kick, bass, hook, hats]            # Parts made outside orch.part join the mix here
bass.duck, hook.duck = 6, 4                       # dB of sidechain pumping on every kick
hook.sweep = True                                 # its expr curve drives a 24 dB ladder low-pass
hook.expr((B(5), cut(500)), (B(11), cut(4500)))   # the filter opens across the build
```

- `surge(patch)` fetches the factory patch once into `STUDIO_HOME/surge/patches` and plays every note on the grid. `python <skill>/surge.py list Basses` prints the names to choose from.
- Patches come out anywhere between -13 and -32 LUFS on the same phrase. Render once at `gain=0`, then set each `gain` from the stem report.
- Surge kicks and toms are pitched: the kick on the key's root (`a1` in A minor), toms on chord tones.
- `synth` voices read their brightness from the part's `expr` in `cut(hz)`: keep ticks between 3 and 6 kHz, above a voice.
- Depths that worked on Launch: 6 dB on basses and pads, 4 dB on the hook, 9 dB on a drone.
- A hard stop after the final hit: `p.vol((t - 0.15, 0), (t, -120), (999, -120))` on every part but the ring-out.
- Before choosing a patch, render the candidates on the same phrase, normalized, one after another in a single file with an index of start times, and let the user pick by ear.

## Patches measured

One phrase per role at 110 BPM in A minor; level in LUFS, brightness as spectral centroid. Starred patches played in Launch.

| Role | Patch | Measured |
|---|---|---|
| Kick | `Percussion/Kick Tech 1`* | punchy, the most click: 189 Hz, -15 |
| | `Percussion/Kick Tech 2` | deeper: 141 Hz, -16 |
| Snare | `Percussion/Snare Tight`* | tonal and low: 431 Hz, -25 |
| Toms | `Percussion/Synth Tom 3`* | deep: 70 Hz, the loudest of the three |
| Rolling bass | `Basses/Rubber Bass`* | round: 50 Hz, -17 |
| Distorted bass | `Basses/Dist Bass 1`* | gritty mids: 166 Hz, -18 |
| | `Basses/Rumble` | pure sub: 49 Hz, -15 |
| Hook | `Plucks/Saw Pluck`* | 1.1 kHz, wide |
| | `Plucks/Fog` | darker: 776 Hz, wide |
| | `Plucks/Sync Pluck` | the brightest: 1.8 kHz |
| Pad | `Pads/MKS-70 Warm Pad`* | warm: 188 Hz, the widest |
| Drone | `Basses/Eighties Drone`* | low mids: 249 Hz |
