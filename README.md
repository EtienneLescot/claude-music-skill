# claude-music-skill

**Claude composes, a local model performs.** A Claude skill that turns a one-line request into a full instrumental track in any style:

1. **Brief.** Claude expands « une musique électro un peu deep, avec un crescendo » into a detailed brief: style, tempo, key, a timeline in seconds, instruments, energy curve, mix. You approve it.
2. **Score.** Claude writes the music as [Strudel](https://strudel.cc) code (TidalCycles for the browser): form, harmony, arrangement, mix. The score is the source of truth and plays as-is on strudel.cc.
3. **Ear.** Claude cannot hear, so `ear.html` renders the score offline, draws a spectrogram and measures every section (levels, bands, attacks, novelty, clipping). Claude fixes what it sees before going further.
4. **Performance.** Strudel alone sounds synthetic. [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5), running on your own GPU, performs the whole mix in four takes while keeping the score's timing and form.
5. **Finish.** Each take gets the draft's bar-by-bar dynamics back (AI covers flatten them), then a true-peak limiter to -14 LUFS. You pick the take you prefer.

Everything runs locally. No text-to-music service is involved: the musical decisions are Claude's, the model only gives them a sound.

## Install

```bash
git clone https://github.com/EtienneLescot/claude-music-skill
cp -r claude-music-skill/strudel-composer ~/.claude/skills/
```

Then install ACE-Step 1.5 and set `ACESTEP_DIR`: see [strudel-composer/README.md](strudel-composer/README.md). You need an NVIDIA GPU (4 GB of VRAM minimum, tested on 12 GB), Python 3.11 or 3.12 with [uv](https://docs.astral.sh/uv/), and a browser Claude can drive (Claude's built-in browser, Claude in Chrome or Playwright) for the ear.

## Use

Ask Claude Code for music in your own words:

> une musique électro un peu sympa, un peu deep, avec un crescendo

> 50-second launch film score, 110 BPM, A dorian, dark and driving, with a breakdown for a voice-over at 0:34

Claude shows the brief, composes, checks the score with the ear, performs it, and gives you the score, a strudel.cc link and four finished takes.

## What is inside

| Path | Role |
|---|---|
| `strudel-composer/SKILL.md` | The skill: pipeline, brief template, genre conventions, composition and mixing rules, sound palette |
| `strudel-composer/ear.html` | Offline Strudel renderer and analyser: spectrogram, metrics, stems, buses, comparison, dynamics transfer |
| `strudel-composer/serve.py` | Local static server that also accepts `PUT` of `.wav` files, so the ear can save renders |
| `strudel-composer/perform.py` | ACE-Step performance, dynamics transfer, BS.1770 loudness meter and limiter, with a self-check |

## Lessons from building it

- **The score matters most.** At cover strength 0.9 the model follows the composition closely, and that is what listeners preferred. At 0.3 to 0.5 it keeps the beat grid but loses the form and sounds generic.
- **Cover the whole mix.** Covering instrument buses one by one loses the interplay. Sampled instruments and a hand-written analog chain were also tried and did not beat the whole-mix cover.
- **Metrics check the score, not the taste.** The take listeners preferred was flagged as muddy and had the lowest fidelity score of five. The skill presents every take at equal loudness and lets you choose.
- **Strudel's offline export needs care.** `ear.html` works around five issues in `renderPatternAudio` (Strudel 1.3): render cost growing with the square of the length, a polyphony cap that silently drops notes, reverb impulses not awaited, samples not awaited, and audio nodes recycled across render contexts. With the workarounds, two renders of the same score agree within 0.5 dB.

## Licences

- This repository: MIT, see [LICENSE](LICENSE).
- Strudel is AGPL-3.0. `ear.html` loads it from a CDN and does not redistribute it.
- ACE-Step 1.5 code is MIT. Check the licence of its model weights before any commercial use.
- Strudel's sample banks (dough-samples, VCSL, tidal-drum-machines) carry their own licences.
