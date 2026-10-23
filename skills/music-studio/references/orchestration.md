# Orchestration

Who plays what, where, and with whom. Pitches are sounding pitches in scientific notation (`c4` is middle C).

## Ranges in this studio

"Plays" is what the samples cover: a note outside it is silent, and the orchestra warns before rendering. "Best" is where the instrument sounds full and idiomatic; outside it, write sparingly and on purpose.

| Instrument | Plays | Best | Character |
|---|---|---|---|
| violins, violins 2 | g3-c7 | d4-a6 | the lead voice of the orchestra; above e6 thin and brilliant |
| violas | c3-c6 | c3-e5 | warm inner voice; doubles melodies an octave down |
| celli | c2-c#5 | c2-a4 | the most singing register is a3-a4; the floor with the basses below |
| basses | c1-c4 | e1-g3 | the real bass; usually doubles celli an octave down |
| flute | c4-c7 | g4-a6 | soft and breathy low, bright and floating high |
| harp | c2-c7 | c2-c7 | arpeggios, glissandi feel, single bell notes doubling a melody |
| horns | e2-f5 | a2-c5 | heroic in unison (f3-f4), warm pads in chords; high notes strained |
| trumpets | e3-e6 | c4-a5 | fanfare and climax; one trumpet carries over a whole orchestra |
| trombones | e2-f5 | e2-f4 | power chords and chorales; the weight of a tutti |
| bass trombones | e1-g4 | b1-d4 | under the trombones, the snarl of the low brass |
| tuba | e1-d4 | f1-a3 | the foundation of the brass; roots only |
| timpani | c2-c3 | d2-c3 | tuned to the chord roots; hits on strong beats, rolls into arrivals |
| choir sopranos | any | f4-d5 | held vowels and syllables, the top of the tutti |
| choir altos | any | c#4-f4 | warmth inside the chord |
| choir tenors | any | d3-a3 | the epic male sound with the basses |
| choir basses | any | g2-d3 | the power under the choir |

Untuned percussion (bass drum, big drum, snare, tenor drum, cymbals, anvil) plays `hit()`; its pitch does not matter.

**Long articulations play one note at a time in the open mode.** Sonatina's legato patches (strings, horns, trumpets, trombones, tuba, flute) are monophonic: a note that starts under a held one becomes a legato transition, and a chord leaves one voice that is never released. Write chords by giving each note its own part (`violins`, `violins 2`, `violas`, `celli`; or several parts of one instrument with `name=`), or use `tremolo` or `short`, which take chords, as does `bass trombones` long. The orchestra warns before rendering when a long part is given a chord. In Discover mode long parts take chords.

## The layers of a texture

Every texture is built from up to seven layers. Name them before writing, and give each its own register and rhythm.

1. **Melody**: one line, the loudest musical idea.
2. **Counter-melody**: a second line that moves when the melody holds, in another register.
3. **Harmony**: sustained chords or a pad, in the middle register, never louder than the melody.
4. **Bass**: roots and fifths, or a stepwise line, under c3.
5. **Rhythmic engine**: an ostinato (spiccato strings, repeated brass) that sets the pace.
6. **Percussion**: accents and transitions, not a constant beat (unless the style asks for one).
7. **Colour**: harp, flute, cymbals, a choir pad; used for moments, not throughout.

A quiet section uses two or three layers; a climax uses all seven. If two layers share a register and a rhythm, one is redundant.

## Doublings

- **The melody in octaves** is the film-score sound: violins high with horns an octave lower, or trumpets with violins an octave higher. Three octaves (violins, trumpets or horns, trombones or celli) for the biggest moments.
- **Unison** doublings blend: horns with celli, flute with violins, choir with strings.
- **Never thicken the melody with thirds in the low register**; in the high register thirds are sweet (two flutes, violins divided).
- **Bass**: celli with basses an octave lower; tuba or bass trombone added at the climax.

## Balance

The catalog's levels are calibrated so that a part at full expression sits where it should; adjust with `gain` from the stem report.

- At the same dynamic, one trumpet or one trombone is about as loud as two horns; the brass at forte cover the strings unless the strings play in octaves.
- The melody sits 3 to 6 dB above the accompaniment; the choir 6 to 9 dB under the brass at a climax, unless it carries the melody.
- In a soft section, the melody instrument alone is audible over a pad; write the pad an octave away from it.

## Tutti recipes

- **Epic climax**: violins and trumpets on the melody an octave apart, horns the octave below; trombones and tuba on roots and fifths in the rhythm of the ostinato; celli, violas and violins 2 on the spiccato ostinato; choir on held chords; timpani and big drum on the strong beats; a cymbal on each new phrase.
- **Warm swell**: celli and horns in unison on the melody, violas and violins 2 holding the chord above, basses on the root, harp arpeggios, no percussion.
- **Mystery**: violins tremolo high and soft on a fifth, celli and basses holding a low pedal, a horn or flute fragment of the motif, a timpani roll that swells and dies.

## Idioms that sound real, and ones that sound fake

Sounds real with these samples:

- Long legato lines with an expression curve, phrase by phrase.
- Spiccato ostinati with accents on the metre (`3+3+2` in 4/4, the first and fourth eighth in 6/8).
- Brass swells (expression from 60 to 120 over a bar) and short brass hits on strong beats.
- Tremolo strings as a pad or a build, timpani rolls with a fader swell into an arrival.
- Held choir chords on open vowels.

Sounds fake, avoid or hide:

- Fast scalar runs and trills in the strings or flute: samples cannot play them evenly. Use a cymbal swell or a harp sweep instead.
- An exposed solo melody with no expression curve: always shape it.
- Repeated notes at one velocity: always vary the velocity with the metre.
- Very short notes on long patches, and long notes on short patches.
- The choir singing a fast melody note by note: give it held notes and syllables.
- Everything at full expression all the time: dynamics are half of realism.
