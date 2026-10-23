# The composer's method

How a working film and media composer gets from a request to a finished cue. Follow it in order; each step has a deliverable you can check before moving on. The other references go deeper: `melody.md`, `harmony.md`, `orchestration.md`, `critique.md`, `culture.md`, and one sheet per style in `styles/`.

## 1. Brief

Turn the request into eight lines at most, and show them to the user.

- **Identity:** style (pick the closest sheet in `styles/`, or two to blend), mood in three words, tempo and metre, key and mode, duration.
- **Purpose:** where it plays (a trailer, a game menu, a social post, under a voice-over). A social post must grab in the first two seconds; music under a voice must leave the 300 Hz to 3 kHz band and the rhythm free.
- **Timeline:** sections with bars and seconds.
- **Energy curve:** where it builds, breaks, peaks. The peak sits at 60 to 75 % of the length.
- **Orchestration:** who carries the melody in each section, what holds the floor.

Ask only when a structural choice is open and costly (a fixed duration, room for a voice). Otherwise decide and say what you decided.

## 2. Reference DNA

Name two or three reference styles or composers (never a single track to imitate), then write down their DNA: tempo, metre, mode, harmonic rhythm (chords per bar), typical progression, melodic traits, rhythmic signature, orchestration, form, and the one or two signature devices that make the style recognisable. The style sheets give this ready-made; adjust it to the request. The goal is the style's grammar, never its melodies.

## 3. Motif first

Write the hook before anything else, alone, as a line of (pitch, eighths). Check it against `melody.md`: range, contour, rhythmic identity, repetition with variation, a high point placed late. Write two or three candidates and keep the strongest; say why in one line. Everything else serves this melody.

## 4. Harmony

Choose the progression that carries the emotion (`harmony.md`), the harmonic rhythm, and where the cadences fall. Check that the melody's long notes land on chord tones or on deliberate, resolving tensions. Plan any modulation (a lift a whole step up for the last chorus, a shift a third away for a change of scene).

## 5. Form and energy map

Lay out every section in a table: bars, what the melody does (stated, developed, fragmented, in full), density (how many layers), register span, and a target loudness. Contrast is the composer's main tool: something must change at least every 8 bars (instrument, register, density, harmony, rhythm). Hold back: the first statement is small, the climax uses what was saved.

## 6. Orchestration

Assign the layers (`orchestration.md`): melody, counter-melody, harmony, bass, rhythmic engine, percussion, colour. Respect the ranges; double the melody in octaves, never in thirds in the low register; give the low end roots and fifths. In this studio, the orchestra prints a warning for every note outside an instrument's range: fix them all.

## 7. Detail pass

This is where a mockup becomes a performance.

- Every sustained phrase gets an `expr` swell that follows the line's shape; dynamics breathe at the phrase level, not the bar level.
- Shorts get accented velocities that follow the metre (strong beats and syncopations), never a flat velocity.
- Legato lines for melodies; repeated notes re-articulated, never tied.
- Transitions: a cymbal swell or a roll into a new section, a fill on the last beat, a silence before a drop.
- The ending is composed, not faded: a final chord with a roll, a button (one short tutti hit), or the motif returning small.

## 8. Render, listen, judge

Render, run `listen.py`, open the spectrogram, then go through `critique.md`: the score checks, the render checks, the three questions. Change one thing per pass, at most three passes, and say what changed and why.

## 9. Deliver

Deliver the WAV, the stems and the score, with what you measured and what you would try next. When there are real alternatives (two hooks, two endings), render them and present them at equal loudness, side by side; the user's ear decides, never the metrics.

## Taste

These hold across styles; they are what separates a composer from a sequencer.

- **The melody is king.** If a listener cannot hum it after one hearing, no orchestration will save the cue.
- **Earn the climax.** A climax is loud only relative to what came before: start smaller than you think, keep something back (the top octave, the choir, the drums) for the moment that counts.
- **One idea per section.** A section develops one idea; more ideas make it busier, not richer.
- **Space.** Leave registers empty, let notes ring, use silence before an arrival. Density everywhere is the sign of an amateur.
- **Contrast beats volume.** Light against dark, high against low, sparse against full, legato against staccato.
- **Repetition with variation.** Repeat enough to be remembered, vary enough to stay alive: the same melody in a new register, a new harmony under it, a new rhythm around it.
- **Clichés are tools, not goals.** A trailer braam or a pop progression works because it is familiar; use it on purpose, once, where it lands hardest.
- **Finish well.** People remember the opening and the ending most; spend time on both.

## Originality

- Never quote or closely paraphrase a known melody, even a few notes of a famous opening (film themes, pop hooks, anthems). Styles, progressions, rhythms and orchestration are free; melodies are not.
- If a hook sounds familiar, change two of: its rhythm, its contour, its starting degree, its interval of the leap.
- Name reference composers for style only, and say so to the user; never promise a "sound-alike" of a specific track.
