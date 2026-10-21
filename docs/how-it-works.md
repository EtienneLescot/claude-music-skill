# How it works

A coding agent cannot hear. Everything in this skill is built around that fact: the agent writes music as code, a renderer turns it into audio the agent can measure and look at, and a local model gives the result a human sound.

## 1. Brief

A request like « une musique électro un peu deep, avec un crescendo » becomes a seven-part brief before any code:

| Part | Example |
|---|---|
| Identity | deep house, warm and hypnotic, 122 bpm, F minor, 1:42 |
| Timeline | intro 0:00 (8 bars) · groove 0:16 (16) · breakdown 0:47 (8) · full groove 1:03 (16) · outro 1:34 (4) |
| Instruments | soft 909 kick, shuffled hats, sine sub bass, Rhodes chords, airy pad, kalimba motif |
| Energy | rises through the groove, dips at the breakdown, peaks in the full groove |
| Mix | warm, round lows, soft top, wide pad |
| Constraints | no harsh highs, no busy fills |
| Performer caption | warm deep house, soft punchy kick, shuffled hi-hats, round sub bass, dusty Rhodes chords… |

The skill carries genre conventions (tempo ranges, typical forms, core instruments, caption starting points) for deep house, techno, lo-fi, ambient, cinematic, synthwave, drum and bass and hip hop, and fills every gap the request leaves.

## 2. Score

The brief becomes the header of a [Strudel](https://strudel.cc) file. Each instrument is one `$:` line, gated by a timeline mask that reads like a DAW arrangement:

```js
//                                         intro  groove  break  full   outro
$: s("bd*4").bank("RolandTR909").mask("<   1!8    1!16    0!8    1!16   0!4>")
```

The score is the source of truth. It plays as-is on strudel.cc, and everything else is derived from it.

## 3. The ear

`ear.py` opens `ear.html` in a headless Chromium, which renders the score offline with Strudel's own engine, faster than real time, and reports:

- a log-frequency spectrogram, gridded by bar, saved as a PNG the agent opens;
- per-section levels, band energies, brightness, attack density and novelty (does the section change anything?);
- flags with their usual fix: clipping, too quiet, muddy, dull, static arrangement, silence, mono, missing sound.

It also renders each layer alone (stems) to find the culprit behind a flag, compares renders of the same score, and saves the draft WAV. Agents that drive a browser can also use the page interactively through `serve.py`: instrument buses, mixing, dynamics transfer.

Sounds: Strudel's drum machines, synths and sample banks, plus the 128 General MIDI soundfonts (strings, brass, winds, choir, guitars), the same palette as strudel.cc.

## 4. Performance

Strudel alone sounds synthetic. `perform.py` hands the draft to [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) on the local GPU, in its `cover` mode: the model re-performs the whole mix in the style of the caption while keeping the score's timing and form.

The settings come from listening tests on the same score:

| Tried | Result |
|---|---|
| Cover strength 0.3 to 0.5 | keeps the beat grid, loses the form, sounds generic |
| **Cover strength 0.9, whole mix** | **preferred** |
| Starting from noise (`--source 0`) | keeps rhythm and form, rewrites the chords: 60 % of bars keep the draft's chord |
| **Starting from the draft (`--source 0.5` and `0.85`)** | **68 to 72 % of bars keep the chord; 0.85 keeps synth timbres** |
| Cover of each instrument bus separately | loses the interplay |
| MIDI to sampled instruments (Salamander, VSCO, no AI) | real instruments but mechanical playing |
| Hand-written analog DSP chain on the stems | well measured, still synthetic |

## 5. Finish

AI covers keep the timing but flatten the dynamics: a crescendo becomes a wall. Each take gets the draft's bar-by-bar level curve back, then a true-peak limiter brings it to -14 LUFS and -1 dBTP with a hand-written ITU-R BS.1770 meter. Every take ends at the same loudness, so the listener compares sound, not level.

Four takes are made, two seeds at two source levels, and all four are presented. In testing, the take the listener preferred had the lowest fidelity score of five: the metrics check the score, never the taste.

## Making Strudel render offline reliably

Strudel's offline export (`renderPatternAudio`, version 1.3) had issues that made renders silently lose notes. `ear.html` works around them:

1. **Quadratic cost.** Every note stays in the audio graph until the end, so 48 bars took 190 s. The ear renders 4-bar chunks with a tail and sums them: 16 s.
2. **Polyphony cap.** The 128-voice limit applies to every scheduled note offline, dropping whole layers. Raised to 4096.
3. **Reverb impulses not awaited.** Generated asynchronously, they arrived after rendering started. The ear holds each render until they exist.
4. **Samples not awaited.** A note whose sample arrived late was dropped. The ear counts downloads and decodes in flight and waits.
5. **Audio nodes recycled across contexts.** A global node pool reused nodes from a finished chunk in the next one; the connection failed silently. Nodes of a closed context now look garbage-collected to the pool.
6. **Soundfonts lost at start-up.** Registered alongside the sample banks, they were sometimes overwritten. They are now registered after the banks.

Two renders of the same score now agree within 0.5 dB.
