# How it works

## The idea

A 3D object can come from a model trained to output 3D, or from an agent driving Blender. This skill takes the second road for music: the agent does what a composer does with a virtual orchestra (writing, orchestration, articulations, expression, mix), and real recordings of instruments play it. The skill is the studio: an engine, an orchestra, a choir, an ear.

How the project arrived at this design, and what was tried and dropped on the way, is in the [research log](research-log.md).

## The files

| File | Role |
|---|---|
| `studio.py` | the engine: parts (notes, syllables, CC1 expression, fader automation), rendering through sfizz, DawDreamer or the choir, mixing with pedalboard, a Dragonfly hall, a BS.1770 loudness meter and a true-peak limiter |
| `orchestra.py` | the catalog: a score asks for `('horns', 'long')`; the orchestra picks the source, the seat, the room send and a level calibrated so the same score balances in both modes |
| `sing.py` | the choir: singing-voice models sing the score's syllables, six singers per section, and BigVGAN turns them into sound |
| `discover.py` | the optional source: BBC Symphony Orchestra Discover hosted headless, its keyswitches, and the capture of its instruments |
| `theory.py` | roman numerals and chord symbols to notes, so a score writes harmony rather than pitch arithmetic |
| `references/` | the composer's craft, read step by step: method, melody, harmony, orchestration, critique, musical culture, ten style sheets |
| `listen.py` | the ear: loudness per section, energy per band, width, each stem's level, a spectrogram with the sections marked |
| `setup.py` | installs the tools, the samples, the voices and the vocoder; `--capture` saves Discover's instruments |
| `bigvgan_onnx.py` | converts BigVGAN to ONNX once, at setup |
| `requirements.txt` | what `uv run --with-requirements` installs for every command |

## The composer's craft

Knowing the tools is not composing. The skill carries a composer's method in `references/`, read by the agent at the step that needs it, so the musical choices are deliberate and the same from one request to the next:

- **Method:** brief, reference styles reduced to their grammar, the motif written first and tested, harmony, a form with an energy target per section, orchestration, a detail pass, critique, delivery. Plus the taste that separates a composer from a sequencer (earn the climax, one idea per section, space, contrast) and the originality rules (styles are free, melodies are not).
- **Melody, harmony, orchestration:** what makes a hook, how to develop a motif, progressions by emotion, cadences and modulations, ranges measured on this studio's samples, layers, doublings, balance, the idioms that sound real with samples and the ones that sound fake.
- **Ten style sheets:** epic trailer, adventure, heroic, emotional, wonder, dark suspense, swashbuckler, waltz, march, cinematic pop; each with tempo, harmony, melody, rhythm, orchestra, form, signature devices, pitfalls, and the catalog's instruments for it.
- **Culture:** what each period and tradition, from Baroque to trailer music and pop, contributes as technique.
- **Critique:** checks on the score before rendering, targets on the render, and the questions that make the user's listening specific.

Two checks run in code: the orchestra warns before rendering about every note an instrument's samples cannot play (silent) or plays poorly, and `theory.py` turns `I V vi IV` in D into chords, so harmony is written as harmony.

## The orchestra

The open mode plays [Sonatina Symphonic Orchestra 4.0](https://github.com/peastman/sso): real string and brass sections with legato, staccato and tremolo, woodwinds, harp, timpani and drums. Its performance patches take the volume of long notes from CC1 and of short ones from velocity, so every sustained phrase gets an expression curve. Setup fetches only the patches the catalog names and the samples they use.

Sonatina has no timpani rolls and no cymbal swell, and no large drum or anvil: five [VSCO 2](https://github.com/sgossner/VSCO-2-CE) folders fill in. The skill writes their SFZ itself: hits layered by dynamic with round robins, and timpani rolls measured drum by drum and mapped to the keys around their pitch.

Every part is placed in one virtual room: a pan, a send to a Dragonfly hall (a 30 m scoring stage, 2.6 s), a high-pass where the low end would muddy the mix. The master goes through a gentle bus compressor (-14 dB, 2:1, so the contrast between sections survives) and a true-peak limiter to -14 LUFS, -1 dBTP.

## The choir

No open choir library has vowels and legato, and sampled choirs sound like a synth pad. The choir is sung instead, the way OpenUtau sings, without OpenUtau: [DiffSinger](https://github.com/openvpi/DiffSinger) voicebanks are ONNX models that take phonemes, their durations and a pitch curve.

- **From the score:** each note has a syllable; `sing.py` places the consonants before the beat so the vowel lands on it.
- **The pitch curve:** 40 ms glides between notes, a vibrato that grows in after a quarter second, a slow drift.
- **Dynamics:** the voice's soft and loud timbres blend along the CC1 curve, and the curve and velocities also set the gain.
- **A section:** six singers, each with their own timing (about 15 ms), tuning (about 7 cents), vibrato, formant and timbre, spread across the stereo field.
- **The voices:** Hoshino Hanami (LotteV) for sopranos and altos, Namine Ritsu (Canon) for tenors and basses. Both allow commercial use.

The vocoders shipped with DiffSinger voices are non-commercial (CC BY-NC-SA). NVIDIA's [BigVGAN v2](https://github.com/NVIDIA/BigVGAN) (MIT) replaces them: DiffSinger's mel bands (40 Hz to 16 kHz) are mapped back to a linear spectrum and onto BigVGAN's bands, which keeps the pitch within 1 %. Converted to ONNX, it runs seven times faster than real time on a GPU through DirectML.

## Discover, the optional source

[BBC Symphony Orchestra Discover](https://www.spitfireaudio.com/products/bbc-symphony-orchestra-discover) sounds clearly better: its sections are recorded together in one hall with one curated mic mix. It is free but closed: encrypted samples, Spitfire's plugin only, an account and an app that requires administrator rights.

- **Hosting:** DawDreamer runs the plugin headless; keyswitches pick the articulation (strings: 0 long, 1 spiccato, 3 tremolo; brass: 0 long, 1 staccatissimo; percussion: 0 timpani, 1 untuned, each instrument on one key).
- **Instruments:** choosing one is not a plugin parameter and the presets are encrypted, so each user saves eleven instrument states once (`setup.py --capture`). They hold Spitfire's patch data, which its terms (clauses 5 and 8) forbid redistributing: the project ships none.
- **What it lacks:** timpani rolls become fast hits whose velocity follows the swell, a cymbal swell becomes strokes growing louder. Harp, flute, the sub and the choir come from the open sources.

## The ear

The agent reads `listen.py`'s numbers and the spectrogram, never the music. What it checks: the contrast between sections in LUFS (the climax 3 to 5 above the theme), the weight (sub and low bands), the brightness, the width, and whether the melody sits 3 to 6 dB above the accompaniment. The numbers check the render; the listener decides.

## Next

- More voices with open licences, to vary the timbre within a section, and a faster choir on CPU.
- [VCSL](https://github.com/sgossner/VCSL) (CC0): more percussion layers and round robins.
