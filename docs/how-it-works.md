# How it works

## The idea

A 3D object can come from a model trained to output 3D, or from an agent driving Blender. This skill takes the second road for music: the agent does what a composer does with a virtual orchestra (writing, orchestration, articulations, expression, mix), and real recordings of instruments play it. The skill is the studio: an engine, an orchestra, an ear.

## The studio

| File | Role |
|---|---|
| `studio.py` | the engine: parts (notes, CC1 expression, fader automation), rendering through sfizz (SFZ libraries) or DawDreamer (VST3 instruments), mixing with pedalboard, a Dragonfly hall, a BS.1770 loudness meter and a true-peak limiter |
| `orchestra.py` | the orchestra: a score asks for `('horns', 'long')`; the orchestra picks the source, the seat, the room send and a level calibrated so the same score balances in both modes |
| `listen.py` | the ear: loudness per section, energy per band, width, each stem's level, a spectrogram with the sections marked |
| `setup.py` | installs sfizz, Dragonfly and the open samples; captures Discover instruments on the user's machine |

Bricks the skill builds itself, because the libraries ship as raw recordings:

- **SFZ from sample names**: VSCO 2 ships WAV files named by note and dynamic; the skill writes the mapping, with dynamic layers crossfading on CC1 so a crescendo changes the timbre (measured on a horn: +11 dB and a brightness from 695 to 1278 Hz).
- **Decent Sampler to SFZ**: Virtual Playing Orchestra's choirs and basses ship as `.dspreset`.
- **Legato**: a note starting under a held one skips its attack and fades in.
- **Sections from soloists**: a part played several times, detuned by a few cents, with its own timing and stereo spread.
- **Timpani mapped by pitch**: each VSCO drum is measured and mapped to the keys around it.
- **Discover rolls and swells**: Discover has timpani hits only, so a roll becomes fast hits whose velocity follows the swell.

## What the listening tests taught

The skill got here by elimination, each step judged by ear:

| Approach | Verdict |
|---|---|
| Strudel code, then ACE-Step 1.5 re-performing the draft | synthetic, or the harmony rewritten |
| ACE-Step generating natively from a Claude-written plan | « pas au niveau d'une musique de film » |
| Open-weight music models in general | independent ranking (Artificial Analysis Music Arena, Oct 2026): the best is 13th on instrumental |
| A studio with free sample libraries (VSCO 2, VPO) | « beaucoup mieux, on est sur la bonne voie » |
| More instruments, same writing | « complexifié, mais la couleur générale n'est pas changée » |
| Writing like a blockbuster: a real theme, octaves and open fifths, a floor, a stop before the climax | correct, but the samples cap it |
| The same score on BBC Symphony Orchestra Discover | « bien meilleur que tout ce qu'on a fait avant » |

Two lessons hold: **the writing makes the colour** (octaves and fifths, a strong motif, dramatic contrast), and **the recordings set the ceiling** (one hall, real sections). Hence two modes.

## Why Discover is better, and why it is optional

Discover's sections are recorded together in one hall with one curated mic mix; the open libraries mix solo players, small sections and different rooms. Discover is free but closed: its samples are encrypted, it plays only through Spitfire's plugin, it is installed through an app that requires an account and administrator rights. The skill hosts the plugin headless (DawDreamer) and drives it with keyswitches (strings: 0 long, 1 spiccato, 3 tremolo; brass: 0 long, 1 staccatissimo; percussion: 0 timpani, 1 untuned, with the bass drum on 48, suspended cymbal 53, anvil 57, piatti 71).

Choosing an instrument is not a plugin parameter, and the presets are encrypted, so each user saves eleven instrument states once (`setup.py --capture`). Those states contain Spitfire's patch data; Spitfire's terms (clauses 5 and 8) forbid redistributing patches or any part of a product, so the project ships none.

## The ear

The agent reads `listen.py`'s numbers and the spectrogram, never the music. What it checks: the contrast between sections in LUFS (the climax 3 to 5 above the theme), the weight (sub and low bands), the brightness, the width, and whether the melody sits 3 to 6 dB above the accompaniment. A hard bus compressor flattens the contrast: the default glue is gentle (-14 dB, 2:1).

## Next: better open sources

A search of openly licensed material (October 2026) found nothing that matches Discover for string sections or choirs: no open library records full sections together in one hall. The candidates to raise the open mode:

- [Sonatina Symphonic Orchestra 4.0](https://github.com/peastman/sso) (CC Sampling Plus, 2024): the best open string and brass sections, with legato, marcato and tremolo.
- [VCSL](https://github.com/sgossner/VCSL) (CC0): more percussion layers and round robins.
- [University of Iowa MIS](https://theremin.music.uiowa.edu/MIS.html): anechoic solo brass and winds in three dynamics, to layer into sections.
- [3D-MARCo](https://zenodo.org/records/3477602) (CC BY 3.0): impulse responses of a real concert hall from 13 stage positions, to put every instrument in the same room.
