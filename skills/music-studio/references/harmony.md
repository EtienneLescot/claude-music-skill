# Harmony

Chords are written as roman numerals over the tonic's major scale: upper case major, lower case minor, `b` for a degree borrowed a semitone down. In D: `I` = D, `vi` = Bm, `bVII` = C. `theory.roman('i bVI bIII bVII', 'd')` turns them into chord symbols; `theory.stack('Bm', 'g3')` gives the notes.

## Progressions by emotion

| Feeling | Progression | Notes |
|---|---|---|
| Uplifting, pop, hopeful | `I V vi IV` · `vi IV I V` · `I vi IV V` | the pop axis; one chord per bar; the most familiar sound in the West |
| Epic, tragic, trailer | `i bVI bIII bVII` · `i bVI bVII i` · `i iv bVI V` | minor with its major neighbours; slow harmonic rhythm (one chord per bar or two) |
| Heroic, triumphant | `I bVII IV I` · `I bVI bVII I` · `I IV I bVI bVII I` | major with chords borrowed from minor: noble, brassy |
| Wonder, magic, flight | `I II I` (Lydian) · `I bVI I` · `I III vi` | the raised 4th of Lydian and third-relation shifts sound like flight and awe |
| Adventure, folk, Celtic | `I bVII I` · `I bVII IV I` (Mixolydian) · `i bVII bVI bVII` (Aeolian) | modal, no leading tone; drones and pedals |
| Tender, nostalgic | `I iii IV iv I` · `I V vi IV` with the bass descending by step (V with its 3rd in the bass) | the minor iv in a major key is the sigh; a descending bass line carries nostalgia |
| Dark, menacing | `i bII i` (Phrygian) · `i bvi i` · tritone `i #iv` | half-step relations and tritones; keep the harmony static and let rhythm drive |
| Suspense | one chord with a pedal, or `i` with a moving inner voice | harmony that refuses to move; tension comes from rhythm, register and dissonance |
| Spanish, dramatic | `i bVII bVI V` (Andalusian) | descending bass, ends on the dominant |
| Jazz, warm | `ii V I` with 7ths · `I vi ii V` | needs a rhythm section to sound idiomatic |

## Harmonic rhythm

How often chords change sets the pace more than the tempo does.

- One chord per bar: the default for pop and film.
- Two bars or more per chord: epic, ambient, suspense; the music breathes.
- Two chords per bar: drive, classical, the approach to a cadence.
- Speed up the harmonic rhythm before a cadence or a climax, slow it down after.

## Cadences

- **Authentic** `V I`: closure. Save the strongest one for the end.
- **Plagal** `IV I`, minor plagal `iv I`: an "amen", warm and noble.
- **Half** ends on `V`: a question; ideal at the end of a first phrase or before a climax (a stop on the dominant).
- **Deceptive** `V vi`: the expected arrival denied; extends a phrase or sets up a final statement.
- **Picardy**: a minor piece ending on the major tonic; light after the dark.

## Voice leading

- Keep common tones in the same voice; move the other voices by the smallest step.
- The bass moves more freely: roots, fifths, or a stepwise line (a descending bass under changing chords is one of the most expressive devices there is).
- **Spacing follows the harmonic series:** wide intervals low (octaves and fifths under C3), closer intervals high. A third under C3 is mud.
- In film and epic styles, parallel octaves and fifths are a sound, not a mistake: power chords in the low brass. In lyrical and classical styles, avoid parallel fifths between melody and bass.
- **Suspensions** (4 resolving to 3, 9 to 8) and **pedal points** (a bass note held under changing chords) are the cheapest, strongest ways to add tension and beauty.

## Modulation

- **The lift:** the last chorus a whole step (or a half step) up, straight in, often after a stop or a drum fill. Pure energy, used in countless hits.
- **Pivot chord:** a chord common to both keys (in C, `vi` = Am is `ii` of G) makes a smooth change.
- **Third relation:** jump to a key a major or minor third away (C to E, C to Ab); the film-score move for a change of scene or a revelation.
- **Relative major/minor:** the same notes, a new centre; the cheapest change of colour.
- Announce a modulation with its new dominant when it should feel inevitable; skip the announcement when it should feel like a surprise.

## Colour chords

- **add9 and sus2:** open, modern, cinematic; avoid the 3rd in the low register.
- **sus4 resolving to 3:** longing, release.
- **Major 7th:** dreamy, bittersweet; **minor with added 6th or 9th:** noir, melancholy.
- **The minor iv in major:** nostalgia, a tear.
- **Chromatic mediants** (`I` to `bVI` or `III`): awe, the reveal of a landscape.
- **Clusters and tritones:** horror and suspense; voice them low and soft, or high and thin.
