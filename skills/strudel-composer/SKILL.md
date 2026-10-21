---
name: strudel-composer
description: Compose instrumental music in any style, then have it performed locally by an AI model. You write the score as Strudel code (TidalCycles for the browser), check it with an offline ear (render, spectrogram, metrics), then ACE-Step 1.5 performs it on the local GPU and the takes are finished automatically (dynamics, -14 LUFS). Use whenever the user asks to make, compose, produce or iterate on music, a beat, a loop, a song, a soundtrack or a jingle, in any genre (lo-fi, house, techno, ambient, synthwave, cinematic, classical, drum and bass…), or mentions Strudel.
---

# Strudel Composer

**You compose, a local model performs.** You write the music as Strudel code: form, harmony, arrangement, mix. That is where the musical intelligence lives. Strudel alone sounds synthetic, so ACE-Step 1.5, running on the user's GPU, then performs the whole mix and gives it an organic timbre while keeping your score. You cannot hear: the ear renders, measures and draws the draft for you, and the listener picks among the performed takes.

Everything runs from a shell. Below, `<skill>` is the folder that holds this file (in Claude Code, `${CLAUDE_SKILL_DIR}`), and commands run from the project root, where tracks live in `tracks/`.

## Pipeline

1. **Brief**: turn the request, however short, into a detailed brief, show it, and keep going.
2. **Write** the score in `tracks/<slug>.strudel`, the brief as its header.
3. **Check the score with the ear**: render, fix, save the draft WAV.
4. **Perform** it with `perform.py`: 4 takes by ACE-Step, each finished automatically.
5. **Deliver**: code, strudel.cc link, the 4 takes. The listener chooses.

### 0. Setup (once per machine)

Needs [uv](https://docs.astral.sh/uv/) and network access to the CDNs Strudel loads from. Ask the user before each install below.

**The ear** runs Strudel in a headless Chromium through Playwright, pinned:

```bash
uv run --with playwright==1.63.0 python -m playwright install chromium
```

**The performer, ACE-Step 1.5**, needs a GPU it supports (NVIDIA CUDA, Apple Silicon through MLX, AMD ROCm or Intel XPU; only NVIDIA has been tested with this skill) and about 10 GB of disk. If `ACESTEP_DIR` is not set, it is missing. Point `UV_CACHE_DIR` and `HF_HOME` at a large disk first if the system disk is short. The skill was tested at commit `ca1e85f`:

```bash
git clone https://github.com/ace-step/ACE-Step-1.5 <dir> && cd <dir>
git checkout ca1e85fe9430179831e6bc6be790c332190a3866
uv sync
```

That is the standard install (CUDA, Apple Silicon). AMD and Intel use their own environment: follow ACE-Step's [installation guide](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INSTALL.md) for the platform. Then set `ACESTEP_DIR=<dir>` and self-check with the Python of that install, for the standard one:

```bash
uv run --project "$ACESTEP_DIR" python <skill>/perform.py --check
```

The models (about 5 GB) download from Hugging Face on the first performance. Without a supported GPU, stop after step 3 and deliver the draft and its strudel.cc link.

### 1. Brief

Users rarely write a brief. « Une musique électro un peu sympa, un peu deep, avec un crescendo » is a normal request. Turn it into a full brief before any code, filling every gap with the genre's conventions (table below) and the words the user chose. A detailed request is kept as is and only completed.

A brief has seven parts:

1. **Identity**: style and sub-genre, mood in three words, tempo, key or mode, duration.
2. **Timeline**: each section with its time in seconds and its bars, and what enters, leaves or changes there.
3. **Instruments**: the role and register of each, and the Strudel sound standing in for it.
4. **Energy**: where it rises, where it breaks, where the peak sits (60 to 75 % of the length). A word like "crescendo" or "drop" in the request is a hard requirement.
5. **Mix**: brightness, space, width, loudness.
6. **Constraints**: what to avoid, room for a voice-over, a fixed duration for a video.
7. **Performer caption**: the ACE-Step prompt, written from this brief, naming instruments and production in order of importance.

Show it to the user in at most eight lines, then go straight on: the user wants to hear music, not approve a document, and can interrupt to correct the brief. Stop and ask only when a structural choice is genuinely open and costly to redo (a fixed duration for a video, room for a voice-over, a vocal part).

**Genre conventions** to fill the gaps:

| Style | Tempo | Typical form | Core instruments | Caption starting point |
|---|---|---|---|---|
| Deep house | 118-124 | filtered intro, groove, breakdown, full groove, outro | soft kick, shuffled hats, round sub bass, Rhodes or organ chords, airy pad | warm deep house, soft punchy kick, shuffled hi-hats, round sub bass, dusty Rhodes chords, airy pads, late night, smooth and hypnotic |
| Techno | 125-135 | intro, build, A, break, drop | 909 kick, 16th hats, rolling or acid bass, stab | dark warehouse techno, pounding analog kick, rolling acid bassline with resonance, crisp hi-hats and ride, hypnotic, industrial textures, wide club mix |
| Lo-fi hip hop | 70-90, swung | intro, A, break, A', outro | dusty drums, Rhodes or piano 7ths, soft bass, vinyl crackle | lo-fi hip hop, dusty vinyl crackle, warm Rhodes electric piano chords, mellow boom bap drums with swing, soft upright bass, vibraphone melody, tape saturation, cozy late night |
| Ambient | 60-80 or free | emerge, bloom, fade | drone, slow pads, sparse piano, bells | ambient, slowly evolving warm analog pads, soft felt piano, glockenspiel sparkles, deep sub drone, shimmering reverb, spacious and calm |
| Cinematic electronic | 90-120 | pulse intro, build, peak, breakdown, final hit | 16th pulse, ostinato motif, kick, impacts, risers | dark cinematic electronic score, driving and hypnotic, analog warmth, clear detuned tape piano chords up front, bright plucked analog synth motif in dotted eighths, crisp live hi-hats and shaker, metallic percussion, punchy kick, tight warm bass, wide airy cinematic mix |
| Synthwave | 85-110 | intro, verse, chorus, bridge, chorus | gated snare, arpeggiated bass, supersaw pads, lead | 80s synthwave, gated reverb snare, pulsing arpeggiated bass, lush analog pads, soaring synth lead, neon nostalgic, wide retro mix |
| Drum and bass | 170-176 | intro, build, drop, break, drop 2 | breakbeat, reese or sub bass, pads | liquid drum and bass, fast crisp breakbeats, deep rolling sub bass, atmospheric pads, soulful keys, energetic and smooth |
| Hip hop | 85-100 | intro, verse, hook, verse, hook | boom bap or trap drums, bass, sample-like keys | hip hop instrumental, hard boom bap drums, deep bass, soulful chopped piano, vinyl warmth, head-nodding groove |

Only cinematic is validated by ear so far; treat the other captions as starting points.

### 2. Write

The brief becomes the header of the track file, the contract the code must honour. `@bpm`, `@key` and `@caption` are read by `perform.py`.

```js
// @title Night Bus
// @cycles 48          total length; the ear renders exactly this
// @section 8          section length for the metrics; match your form
// @bpm 84
// @key A minor        ACE-Step keyscale: major or minor only (D lydian → D major, A dorian → A minor)
// @caption lo-fi hip hop, dusty vinyl crackle, warm Rhodes electric piano chords, mellow boom bap drums with swing, soft upright bass, vibraphone melody, tape saturation, cozy late night
// feel: dusty, late, warm · 2:17
// form: intro 0:00 (8) · A 0:23 (16) · break 1:09 (8) · A' 1:31 (8) · outro 1:54 (8)
// layers: drums (MPC60) · bass (sine, root notes) · keys (fmpiano, 7th chords) · lead (vibraphone motif) · crackle
// energy: 2 → 5 → 3 → 6 → 1
// mix: warm, narrow lows, soft top · avoid: bright hats, busy fills
```

One cycle is one bar of 4/4. `setcpm(bpm/4)` sets the tempo. Sections are multiples of 4 cycles. Convert times with `seconds = bars × 240 / bpm`; when the brief is timed to the second, set `@section 1` to get one row per bar.

Then the code. Use one `$:` line per layer. Gate each layer with a **timeline mask** whose counts sum to `@cycles`: it reads like a DAW arrangement view.

```js
setcpm(84/4)
all(x => x.postgain(0.75))   // master fader
//             intro  A      break  A'    outro
$: s("bd ~ ~ bd, ~ sd").bank("AkaiMPC60").swingBy(1/6, 4).gain(0.8)
     .mask("<0!8    1!16   0!8    1!8   0!8>")
$: note("<a1 f1 c2 g1>").s("sine").attack(0.01).release(0.3).gain(0.6)
     .mask("<0!8    1!16   0!8    1!8   1!4 0!4>")
$: chord("<Am7 Fmaj7 C^7 G7>").voicing().s("fmpiano").hpf(200).room(0.3).gain(0.35)
$: n("<[0 2 4 ~] [4 2 ~ ~]>").scale("A4:minor").s("vibraphone").delay(0.3).delaytime(0.357).delayfeedback(0.35).gain(0.3)
     .mask("<0!8    1!16   1!8    1!8   0!8>")
$: s("crackle").gain(0.1)
```

The performer follows your score closely: a better score gives better takes. Spend the effort here.

### 3. Check the score with the ear

```bash
uv run --with playwright==1.63.0 python <skill>/ear.py tracks/<slug>.strudel
```

It renders the score offline (10 to 60 s; run it in the background if your tool has a short timeout), prints the report, and writes next to the score `<slug>.ear.txt`, `<slug>.ear.json`, `<slug>.ear.png` and the draft `<slug>.wav`. `--cycles` and `--section` override the header, `--stems` adds each `$:` layer rendered alone.

**Open `<slug>.ear.png` and look at the spectrogram.** Fix in this order, at most 3 passes after the first clean render:

1. `ok: false` with `error`: the code did not evaluate. Fix the syntax or the function name.
2. `missing`: a sound outside the palette below.
3. `flags`: each carries its usual fix. If the culprit is unclear, re-render with `--stems` before touching gains.
4. A layer missing from the spectrogram: an rms under -45 dBFS in its stem means it is inaudible.
5. Musical checklist: sections look different at the section lines, the main section is at least 2 dB above the intro, something new arrives every 8 to 16 cycles, the ending resolves, harmony shows as horizontal lines between 100 Hz and 1 kHz.

A flag can be right for the genre (`dull` in ambient, where the sub drone dominates the energy): leave it and say why. The last clean render is the draft the performer gets.

### 4. Perform

With the Python of the ACE-Step install, for the standard one:

```bash
uv run --project "$ACESTEP_DIR" python <skill>/perform.py tracks/<slug>.wav
```

- Caption, tempo and key come from the `@caption`, `@bpm` and `@key` header tags of `tracks/<slug>.strudel`; `--caption`, `--bpm` and `--key` override them. Takes land in `tracks/<slug>-takes/`.
- 4 takes by default (seeds 42, 7, 123, 777), cover of the **whole mix** at strength **0.9**, models loaded once: 12 to 30 s per take on an RTX 4070 Ti, plus 40 s of loading. ACE-Step picks the device itself.
- Each take gets the draft's bar-by-bar dynamics back (the model flattens them), then a true-peak limiter to -14 LUFS, -1 dBTP. Every take ends at the same loudness, so the listener compares timbre, not level.
- Run it in the background when the track is long (time grows with duration); it prints one line per take.

Why these settings, from listening tests: lower strengths (0.3 to 0.5) lose the form and sound generic; covering instrument buses separately loses the interplay; samples and hand-written DSP did not beat the whole-mix cover. ACE-Step tends to darken the mix whatever the caption; naming bright instruments in the caption helps a little.

### 5. Deliver

```
**Night Bus** · lo-fi · 84 bpm · A minor · 2:17
▶ Score: <strudel.cc share link>
Takes (all at -14 LUFS): tracks/night-bus-takes/night-bus-s42.wav, -s7, -s123, -s777
Form: intro 8 · A 16 · break 8 · A' 8 · outro 8
Ear (draft): peak -0.5 dBFS · no flags
Can't judge: which take sounds best. Your ears decide.
```

Present all the takes. Never pre-select or rank them with the ear's metrics: in testing, the listener's favourite take had the lowest fidelity score of five, and a render flagged `muddy` with 8 % mids beat cleaner-measuring ones. Never say a track "sounds great". Say what the ear measured.

## Composition rules

These are the habits that separate a track from a loop.

### Form and energy

- Write the form first. A track of 32 to 64 cycles has 4 to 6 sections.
- Draw the energy curve before coding. The peak sits at 60 to 75 % of the length.
- Change happens at section lines: layers enter or leave, filters open, drums switch pattern.
- Inside a section, vary every 4 cycles: `.lastOf(4, x => x.ply(2))` for fills, `<a b>` alternation, `.sometimesBy(0.2, ...)`.

### Harmony and melody

- Choose a key and use `.scale("A:minor")` with `n()` for melodies: wrong notes become impossible.
- Chords: `chord("<Am7 Fmaj7 C^7 G7>").voicing()`. One chord per cycle, or per two cycles with `/2`.
- Bass follows chord roots in octave 1 or 2: `note("<a1 f1 c2 g1>")`.
- Melody is a motif of 3 to 5 notes, repeated with small changes, with rests `~`. Question and answer over 2 cycles: `n("<[0 2 4 ~] [4 2 ~ ~]>")`.
- Keep pads and chords in octaves 3 and 4, leads in 4 and 5.

### Rhythm and groove

- Swing for lo-fi, hip hop and house: `.swingBy(1/6, 4)`.
- Accents rather than flat velocities: `.gain("1 .6 .8 .6")` or `.gain(perlin.range(.5, .8))`.
- Sparser hats in intros: `.degradeBy(0.4)`.
- 3 against 4: a 4-note motif of dotted eighths is `n("0 4 2 5").fast(4/3)`.

### Mix

- Start every track with a master fader under `setcpm`: `all(x => x.postgain(0.75))`. Clipping almost always comes from hits stacking on the beat, not from one loud layer.
- Starting gains, measured in the ear (each sample is recorded at its own level):

| Sound | Starting gain | Note |
|---|---|---|
| `bd` from `RolandTR909` or `RolandTR808` | 0.4 to 0.5 | hot: alone it already reaches -19 dBFS rms |
| other drum machine hits (`hh sd oh rd cp`) | 0.3 to 0.5 | each peaks around -7 dBFS |
| `sawtooth` bass, 16th notes | 0.2 to 0.4 | |
| `sawtooth` lead or motif | 0.6 to 1.3 | short decays read quiet |
| `piano`, `fmpiano` | 0.5 to 1 | |
| `vibraphone`, `glockenspiel`, `brakedrum` and other VCSL sounds | 0.5 to 2 | quiet recordings |
| `white` noise ticks with a short decay | 0.5 to 0.8 | |

- Only kick and bass live below 120 Hz. `.hpf(150)` to `.hpf(250)` on pads, keys and leads.
- Space: `.room(0.2 to 0.5)` on snares and keys. Delay time in seconds, from the tempo: one beat is `60/bpm`.
- Stereo: `.pan(sine.slow(8))` or `.jux(rev)` on one or two layers, never on kick or bass. Detuned tape feel: `.jux(x => x.speed(1.012))`.

### Movement

- **A signal (`sine`, `saw`, `perlin`) is read once, at the start of each event.** On a sound with one event per bar, `.gain(saw.range(0, 1))` stays frozen and `.hpf(saw...)` never moves. Give the sound many events: `s("white*16")`, or `.segment(16)`.
- A signal's arguments cannot be patterns: `saw.range(0, "<0 1>")` is silent. Put the per-bar level in `.velocity("<0!8 1>")`.
- Crescendos and per-bar automation: one value per bar in a timeline string, `.gain("<0.3 0.34 0.38 0.42 0.46 0.5>")`, counts summing to `@cycles` like masks.
- Filter sweeps: `.lpf(sine.range(400, 3000).slow(16))` on a layer with many events per bar.
- Acid lines: `.s("sawtooth").lpf(500).lpq(8).lpenv(4).lpdecay(0.15)`.
- Ambient: long envelopes `.attack(1.5).release(3)`, `.room(0.7).size(6)`, few attacks per second.

## Sound palette

Only these sounds load identically in the ear and on strudel.cc. Anything else ends up in `missing`.

- **Synths**: `sine`, `triangle`, `square`, `sawtooth`, `supersaw`, `pulse`. Noise: `white`, `pink`, `brown`, `crackle`.
- **Drum machines** with `.bank("<name>")`: `RolandTR808`, `RolandTR909`, `RolandTR707`, `RolandTR606`, `LinnDrum`, `AkaiMPC60`, `OberheimDMX`, `EmuSP12`, `KorgMinipops`, `BossDR110`, `AlesisHR16`, `YamahaRX5`. Sounds: `bd sd hh oh cp rim lt mt ht cr rd cb perc sh` (not every bank has every sound; the ear reports a missing one).
- **Keys**: `piano` (Salamander, light and reliable), `kawai`, `fmpiano`, `clavisynth`. Avoid `steinway`: each note is a 7 to 8 MB WAV that the browser often fails to fetch, and the layer goes silent.
- **Mallets and bells**: `vibraphone`, `marimba`, `glockenspiel`, `kalimba`, `balafon`, `tubularbells`, `handbells`, `wineglass`.
- **Strings and winds**: `harp`, `folkharp`, `strumstick`, `dantranh`, `sax`, `saxello`, `harmonica`, `ocarina`, `didgeridoo`.
- **Percussion**: `conga`, `bongo`, `cajon`, `darbuka`, `framedrum`, `timpani`, `tambourine`, `cabasa`, `clave`, `cowbell`, `woodblock`, `agogo`, `guiro`, `sleighbells`, `gong`, `triangles`, `oceandrum`.
- **Texture**: `casio`, `jazz`, `metal`, `east`, `space`, `wind`, `insect`, `crow`.

- **General MIDI soundfonts** (129 instruments, the same as strudel.cc; play them with `note()` or `n().scale()`, starting gain 0.6 to 1):
  - Strings: `gm_violin`, `gm_viola`, `gm_cello`, `gm_contrabass`, `gm_string_ensemble_1`, `gm_string_ensemble_2`, `gm_tremolo_strings`, `gm_pizzicato_strings`, `gm_orchestral_harp`.
  - Brass and winds: `gm_trumpet`, `gm_trombone`, `gm_french_horn`, `gm_tuba`, `gm_brass_section`, `gm_flute`, `gm_piccolo`, `gm_oboe`, `gm_english_horn`, `gm_clarinet`, `gm_bassoon`, `gm_alto_sax`, `gm_tenor_sax`.
  - Voices and pads: `gm_choir_aahs`, `gm_voice_oohs`, `gm_synth_choir`, `gm_pad_warm`, `gm_pad_choir`, `gm_pad_halo`, `gm_pad_bowed`.
  - Keys and guitars: `gm_epiano1`, `gm_epiano2`, `gm_harpsichord`, `gm_church_organ`, `gm_drawbar_organ`, `gm_celesta`, `gm_music_box`, `gm_acoustic_guitar_nylon`, `gm_acoustic_guitar_steel`, `gm_electric_guitar_clean`, `gm_electric_guitar_jazz`, `gm_overdriven_guitar`.
  - Bass: `gm_acoustic_bass`, `gm_electric_bass_finger`, `gm_fretless_bass`, `gm_synth_bass_1`.
  - Percussion: `gm_timpani`, `gm_taiko_drum`, `gm_orchestra_hit`, `gm_steel_drums`.
  - The full list is in `@strudel/soundfonts` (`gm.mjs`). When the brief names a real instrument, use its GM voice in the draft rather than a synth stand-in: the performer follows what it hears.

Never call `samples(...)`: the ear only loads the banks above.

## Reading the ear

| Metric | Meaning | Usual targets for a draft |
|---|---|---|
| `peakDb` | loudest sample | ≤ -1 dBFS |
| `rmsDb` | average level, a rough loudness | -24 to -14 for a draft; the takes are brought to -14 LUFS anyway |
| `bands` | energy share in % per band: sub < 60 Hz, low < 250, mid < 2k, high < 8k, air above | dance: sub+low 50 to 85 · high+air ≥ 2 |
| `centroidHz` | brightness, energy-weighted, so naturally low | dark < 500 · bright > 1500 |
| `onsetsPerSec` | attack density | ambient < 2 · lo-fi 2 to 5 · house and techno 4 to 10 |
| `novelty` | change from the previous section, 0 to 1 | ≥ 0.1 where something enters |
| `width` | side over mid energy | 0.05 to 0.3 |

In dance music the kick dominates rms: judge the energy curve with `high`, `centroidHz` and the spectrogram's brightness too. Two renders of the same code agree within 0.5 dB.

**In the spectrogram**: vertical streaks are hits, horizontal lines are sustained notes, the bottom lane is the level over time with attack ticks on top, red bars mark clipping, white vertical lines are section boundaries labelled in cycles.

The metrics check the score, not the taste.

## Ear tools

- `ear.py --compare tracks/a.wav tracks/b.wav --bpm 110`: spectrograms and `fidelity` of each file against the first (`barLevelCorr`, `onsetF1`, `medianLagMs`, `secondsDiff`, `levelOffsetDb`), written to `a.compare.txt` and `a.compare.png`. Use it to explain a defect the listener heard, never to pick a take.
- `perform.py --finish draft.wav take.wav --bpm 110`: finish an existing take without the GPU. `perform.py --check`: self-check of the loudness meter, dynamics transfer and limiter. A take that times out (ACE-Step aborts after 600 s, usually because another program holds the GPU) is redone alone with `--seeds <seed>`.
- **Interactive page**, for agents that drive a browser: `python <skill>/serve.py 8765` from the project root, then `http://localhost:8765/ear.html?file=tracks/<slug>.strudel` (add `&stems=1`, or `?compare=...&bpm=...`). In the page, `ear.render(code, opts)`, `ear.save(path)`, `ear.renderBuses(code, { drums: [1, 2] }, dir)` (instrument buses that sum back to the mix), `ear.mix([{ path, gainDb }], out)` and `ear.matchDynamics(draft, take, out, { bpm })`. Renders take longer than many tool timeouts: poll `ear.result` instead of awaiting once.
