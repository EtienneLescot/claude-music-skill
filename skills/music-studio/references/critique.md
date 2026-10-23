# Critique

You cannot hear the render. You can read the score, the orchestra's warnings, `listen.py`'s numbers and the spectrogram, and you can ask the user the right questions. Judge in that order; fix one thing per pass.

## 1. The score, before rendering

Read your own score as a composer would read a student's.

- **Melody**: does it pass the checks in `melody.md`? Is it audible in every section where it plays: no other part in its octave and rhythm?
- **Harmony**: do long melody notes sit on chord tones or on resolving tensions? Any third under c3? Any accidental clash between a held note and a moving chord?
- **Ranges**: the orchestra prints every note outside an instrument's range before rendering. Fix them all: outside "plays" the note is silent.
- **Form**: something changes at least every 8 bars? The climax at 60 to 75 % of the length? The first statement smaller than the last?
- **Detail**: every sustained phrase has an expression curve? Shorts have accented velocities? Transitions into new sections? A composed ending?

## 2. The render

Run `listen.py` with the sections, then read the numbers against these targets.

| Check | Target | If not |
|---|---|---|
| Loudness per section | each section differs from the next; climax 3 to 5 LUFS above the theme, a breakdown 4 to 8 below | thin or thicken the arrangement; ease the glue compressor |
| First seconds | within about 10 LUFS of the climax for a social post or a trailer | the opening is inaudible on a phone; raise the intro's instruments |
| Melody against accompaniment | 3 to 6 dB above in the stems | lower the accompaniment or move it an octave away |
| Choir against brass | 6 to 9 dB under at a climax | `gain` on the choir sections |
| sub+low % | 25 to 45 % for film and trailer | add or remove the floor (basses, tuba, timpani, `sub`) |
| high+air % | 2 to 10 % orchestral | brighten with the master high shelf, or an instrument in the top octave |
| Width | 0.2 to 0.5 | check pans; a hall send too high widens and blurs |
| Limiter | under 3 dB of gain reduction | the mix is too dense or too bass-heavy at the peak |

The spectrogram shows what the numbers hide: a gap where a transition should be, a section with no top or no bottom, a final chord cut short.

## 3. The questions for the user

The user's ear decides. Make listening easy and specific:

- Present alternatives side by side at equal loudness (`-16 LUFS` clips of the same bars), never filtered by metrics.
- Ask about one thing at a time, in musical terms: "Is the hook memorable after one listen?", "Does the climax feel earned, or does it arrive too early?", "Does the choir sound real enough, or does it pull you out?".
- When the user says something sounds wrong, ask where (a time or a section) and what it reminds them of; translate it into a change in the score, not in the mix first.

## Iterating

- One change per pass, the biggest problem first: melody, then form, then orchestration, then mix.
- At most three passes; after that, present what you have and what you would try next.
- Say what changed and what you measured, never that it sounds great.
