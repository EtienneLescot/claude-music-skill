# Research log

## Why this log exists

**Goal.** A skill that lets a coding agent make music at the level of Suno or ElevenLabs by using the LLM's musical intelligence, not a specialised audio model. Closed text-to-music services are the competitors, so they are never building blocks. Every tool must be open source or free, and the skill installs it itself.

**Final design, in five lines.**

1. Like an agent driving Blender through MCP, the agent writes the score as Python code: notes, articulations, CC1 expression, fader moves, mix.
2. Real instrument recordings play it from the command line: open libraries through sfizz, Sonatina Symphonic Orchestra 4.0 by default, or BBC Symphony Orchestra Discover hosted headless in DawDreamer when the user has it.
3. The choir is sung, not sampled: DiffSinger voicebanks driven note by note, voiced by NVIDIA BigVGAN v2 (MIT) through ONNX.
4. One algorithmic hall (Dragonfly), a gentle bus glue, a BS.1770 limiter to -14 LUFS.
5. The agent reads an ear (loudness per section, bands, width, spectrogram). Etienne's ear decides.

**How to read it.**

- Phases are chronological. Each one gives the hypothesis, what was built, what was measured, the verdict and the decision.
- Text between « » is Etienne's own words, in French, as he said them.
- Numbers come from the research notes (specs 001 to 005, kept outside this repo), the session transcripts and the git history.
- LUFS figures are integrated loudness per section. Width is side energy over mid energy.
- The code is being rewritten from scratch around the final design. This file is where the history survives.

## Versions

| Version | Commit | Date | What it was |
|---|---|---|---|
| v1.0 | `30ce731` | 2026-10-21 | Strudel score, offline ear, ACE-Step 1.5 cover |
| v1.1.0 | `1934b4b`, tag `v1.1.0` | 2026-10-21 | takes start from the draft audio: 2 seeds × source 0.5 and 0.85 |
| v2.0.0 | `68ee946`, no tag | 2026-10-22 | `music-studio`: Python score, sampled orchestra, open and Discover modes |
| v2.1.0 | `6e0adfa`, tag `v2.1.0` | 2026-10-23 | Sonatina by default, sung DiffSinger choir, BigVGAN vocoder |

## Timeline

### 1. Strudel and a headless ear (2026-10-21)

- **Hypothesis.** An LLM writes Strudel well. If it can "hear" an offline render, it can compose arranged tracks instead of 4-bar loops and share them as a strudel.cc link. No existing project combined offline render, listening section by section and a share link.
- **Built.** `ear.html` renders with Strudel 1.3.0's `renderPatternAudio` in an `OfflineAudioContext`. It reports level, bands, brightness, onsets, novelty and width per section, raises named defect flags, and draws a spectrogram gridded by cycle. `ear.py` later ran it headless through Playwright 1.63.0, so any coding harness could use it.
- **Measured.** Five bugs in Strudel's offline render, all worked around:
  - quadratic cost: 48 cycles took 190 s, fixed by rendering 4-cycle blocks;
  - the 128-voice cap counted every scheduled note and dropped whole layers;
  - reverb impulses arrived after rendering started;
  - samples that loaded late were dropped silently;
  - a global node pool reused nodes from closed contexts, the real cause of random 2 to 18 dB holes.
- After the fixes, two renders differ by 0.5 dB at most. Lo-fi, techno and a 50 s film cue ("Launch") passed with no flag in 2 to 3 passes.
- **Verdict.** On Launch: « ça paraît très synthétique ». His diagnosis: « notre limite, là, en fait, c'est finalement le logiciel. Qui produit le son ».
- **Decision.** Keep Strudel as the score. Look for something that sounds organic.

### 2. Organic sound: ACE-Step cover and a local bake-off (2026-10-21)

- **Hypothesis.** The code writes the score and an audio model performs it. ACE-Step 1.5 in `cover` mode re-performs the Strudel draft with a real timbre and keeps its structure.
- **Built.** ACE-Step 1.5 turbo on an RTX 4070 Ti with 12 GB, 4 to 5 s per cover. A compare mode in the ear: onset F1 and bar-level energy correlation against the draft. `matchDynamics` reimposes the draft's level bar by bar. A BS.1770 meter and true-peak limiter to -14 LUFS.
- **Measured.**
  - Timing survives every strength: onset F1 0.89 to 0.94, median offset 0 ms.
  - Dynamics do not: the draft spans 17 dB, cover 0.8 spans 9 dB, cover 0.3 is flat.
  - Strength 0.9 with a clear caption reaches an energy correlation of 0.84. With the draft's dynamics reimposed: 0.99, mean bar error 0.4 dB.
  - Mids fall from 22 % in the draft to 3 to 8 % in every cover. ACE-Step darkens everything, whatever the caption.
- **Verdict.** Cover 0.8 won: « c'est sûrement celle qui sonnait le mieux ». And: « Et en même temps bizarrement c'est la plus proche de l'original non ? » The 0.9 cover with dynamics was judged to hold up.
- **Bake-off.** Three other local paths on the same score: a cover per bus, MIDI to SFZ samples (Salamander, VSCO 2, MuldjordKit, FreePats), and a hand-written DSP chain at -14 LUFS. On the ear's numbers, samples and DSP looked best: 29 % and 21 % mids, no flags. Verdict: « le meilleur était ce qu'on avait fait auparavant ». And: « ce que je viens d'écouter là n'est pas terrible ».
- **Seeds.** Five seeds of the 0.9 cover. He picked seed 777, the one the ear ranked lowest on arc fidelity (0.88).
- **Decision.** Keep Strudel, then a full-mix cover at 0.9, then dynamics, then the limiter. Band flags stop ranking renders. Closed text-to-music (ElevenLabs, Suno, Udio, Lyria) is rejected as a building block: « on écarte la piste Eleven Labs […] c'est une piste 100% texte to musique ». This became constitution principle VII.

### 3. Skill v1: Strudel composes, ACE-Step performs (2026-10-21)

- **Reframing.** « on n'essaye pas de faire une musique bien, on essaye de faire un skills qui sait faire de la musique dans différents styles ».
- **Built.** `perform.py` renders four seeds with the models loaded once. A brief step expands a one-line request. General MIDI soundfonts entered the ear (125 instruments), after a classical test showed Strudel had no strings: « Strudel n'est sans doute pas suffisant ». The repo went public under MIT, with a harness-neutral `SKILL.md` and a Claude Code plugin named `music-skill`. ACE-Step's weights were confirmed MIT.
- **Measured.** On "Grid Pulse", a synthwave cue, a new chroma measure showed that `cover` from noise keeps the rhythm and rewrites the chords. Chroma similarity was 0.73, and seed 777 kept the draft's dominant note in only 30 % of bars. Starting from the draft audio (`cover_noise_strength`, exposed as `--source`) raised similarity to 0.86. A bossa nova test held 0.93 to 0.96.
- **Verdict.** On Grid Pulse v2: « il n'y a aucune cohérence entre la version synthétiseur only et la version acestep ». He also noted that the organic layer masks the 80s synths he asked for.
- **Decision.** v1.1.0 delivers 2 seeds × 2 levels: source 0.5 sounds more organic, 0.85 keeps the synth timbres. The proof across four styles planned in spec 003 was rendered in part but never validated by ear.

### 4. Native text-to-music with open models (2026-10-22, morning)

- **Trigger.** Grid Pulse, heard again: « c'est vraiment un peu pas terrible en fait ». "Black Flag", a pirate cue in 6/8 and D minor, went through v1.1.0: « les versions S42, S7, etc. sont vraiment trop proches de l'original et tout fait synthétique ». Then: « les résultats sont pas satisfaisants. Je pense qu'on fait un peu fausse route depuis le début. » New target: Suno's level, with a strategy that leans more on the LLM.
- **Diagnosis.** The draft is the ceiling. No `--source` value gives both a real sound and the score's harmony. Only a tenth of ACE-Step had been used.
- **Hypothesis.** Claude as producer around an open generator: blueprint, N candidates, local scorers, repaint, master.
- **Built.** ACE-Step 1.5 turbo (2B) in text2music, from a Claude-written caption with structure tags, with and without its 1.7B planner, two seeds each. A survey of open models: ACE-Step 1.5 XL (MIT), YuE2-3B (CC BY-NC, editable ABC score), LeVo 2, MiniMax Music 3, Stable Audio 3.
- **Measured.** Artificial Analysis Music Arena v1.1 (October 2026, 1,000 prompts, 17 genres, recruited listeners) ranks Suno v6 first. The best open model, MiniMax Music 3, is 13th on instrumental and 11th on vocal. ACE-Step and YuE2 are not ranked. Every "beats Suno v5" claim was self-reported on automatic metrics.
- **Verdict.** « clairement pas au niveau d'une musique de film. C'est pas terrible. »
- **Decision.** The generator is the ceiling, and the LLM was working at the wrong layer. Native generation was dropped. The research had listed three paths: the best open generator, capped near 13th place; an orchestral mockup through a real sample library; a closed generator, already rejected. Etienne's next message reframed the project along the second path.

### 5. The studio pivot (2026-10-22)

- **Framing.** « Si on veut faire un objet 3D, on peut soit utiliser un modèle entraîné à ne sortir que des objets 3D, ou alors on peut utiliser Blender et connecter Claude dessus via son MCP ». The same for music: Claude uses real production tools.
- **Constraint.** Anyone must be able to install the tools with the skill: « Le but, c'est d'éviter des licences commerciales très chères qui casseraient l'accessibilité de notre skill. » REAPER ($60), Ableton and Bitwig were rejected as paid.
- **Built.** Installed on Windows without admin rights and checked to render: DawDreamer 0.9 (VST3 host, offline render), Faust, Surge XT 1.3.4 (2,855 parameters), sfizz 1.2.3. Sounds and effects: VSCO 2 CE (CC0), pedalboard, Dragonfly Hall. Written by us:
  - SFZ files built from sample names, with dynamic layers crossfading on CC1;
  - legato that skips the attack of a note starting under a held one;
  - sections built from detuned soloists;
  - timpani mapped by measured pitch.
- **Measured.** Black Flag rebuilt with 26 VSCO parts, CC1 swells, humanised timing, orchestral seating, one hall, -14 LUFS. It rendered in 30 s. Gotcha: VSCO names octaves one below scientific pitch, except the harp.
- **Verdict.** « C'est beaucoup mieux, on est sur la bonne voie. » The first validated direction.
- **Decision.** The agent is a composer-programmer in front of a virtual orchestra. Push this route further before other styles.

### 6. Writing like a blockbuster, and the glass ceiling (2026-10-22)

- **v2: more instruments.** 1:24, with VPO choirs, a bass section, detuned ensembles, legato and Decent Sampler presets. Sections at -25, -20, -19, -25, -16 and -17.5 dB, width 0.52, no flags.
- **Verdict on v2.** « c'est complexifié avec plus d'instruments, mais la couleur générale n'est pas changée. La mélodie non plus. » And: « Il n'y a pas la couleur blockbuster. »
- **Diagnosis.** Full triads in the middle register sound like MIDI or a video game. The theme moved stepwise with no motif. Only 0.8 % of the energy sat below 60 Hz.
- **v3: rewritten, not reorchestrated.** 48 bars, 59 s.
  - A new theme: an open fifth, a leap of a sixth, a question ending on the dominant.
  - Octaves and open fifths only, in every family.
  - A floor: a sine sub on the roots and pitch-dropping booms. Energy below 60 Hz rose to 14.8 %.
  - Contrast: a breakdown, then a stop on the dominant before the climax. Sections at -20.6, -15.8, -23.5, -12.0 and -13.0 LUFS.
  - A hard bus compressor flattened that contrast. It was eased to -14 dB at 2:1.
- **Verdict on v3.** « Les deux versions sont correctes, hein, mais il manque encore quelque chose au niveau du rendu instrumental, du rendu des chœurs, dans la couleur ». His question: « Qu'est-ce qui, d'après toi, est notre plafond de verre actuellement ? »
- **Answer.** The samples themselves, estimated at about two thirds of the gap.
  - VSCO horns have 3 dynamic layers and violins 2. VPO's choir has one. Film libraries have 5 to 8.
  - Our sections are detuned copies of one player.
  - The choir is a frozen loop on one vowel.
  - Then come per-note performance, rooms that do not match, and the fact that Claude cannot hear.
- **Context.** A landscape study sorted virtual instruments into three families: recordings, modelling and neural. Free auto-installable libraries sit at amateur tier.
- **Decision.** Test the same score on a professional library.

### 7. BBC Symphony Orchestra Discover (2026-10-22)

- **Hypothesis.** If the samples are the ceiling, the same v3 score played by a pro library will be clearly better.
- **Built.** A VST3 part hosted headless by DawDreamer, fed the same MIDI and CC1. Keyswitches choose the articulation: strings 0 long, 1 spiccato, 3 tremolo; brass 0 long, 1 staccatissimo. The percussion key map was measured: bass drum 48, cymbal 53, anvil 57, piatti 71, timpani 48 to 74. Instrument choice is not a plugin parameter and presets are encrypted, so each instrument state was saved once from the plugin window.
- **Measured.** With only strings and horns from Discover: -20.1, -15.1, -20.5, -12.4, -12.3 LUFS. With all 11 instruments from Discover and nothing synthetic: -19.5, -15.3, -21.0, -12.4, -12.0 LUFS, about 4 min 20 of render because each part warms up the plugin.
- **Verdict.** On the hybrid: « en solo, je l'entends clairement », but in the mix « tous les autres instruments font synthétique ». On the all-Discover render: « Le résultat est bien meilleur que tout ce qu'on a fait avant. »
- **Friction.** Discover needs an account, a newsletter sign-up behind hCaptcha, and an app that always runs as administrator, so computer use could not click in it. Etienne: « la friction risque d'être très forte pour un utilisateur qui veut utiliser notre skills pour faire de la musique ».
- **Finding.** Rendering is already low level: once the states exist, Discover renders with no window. The friction lies in how pro libraries are distributed, and no MCP can remove it.

### 8. Skill v2.0.0: music-studio, two modes (2026-10-22)

- **Decision.** Open mode by default: VSCO 2 CE and Virtual Playing Orchestra through sfizz, installed with no account. Discover mode when the plugin is present. The same score renders in both.
- **Calibration.** Levels are set per mode so the score balances in both. Open against Discover: intro -22 and -20, theme -17 and -15, break -22 and -21, climax -12 and -12 LUFS.
- **Licence.** Music made with Discover is royalty-free. Spitfire's EULA clauses 5 and 8 forbid redistributing patches, so no instrument state ships. `setup.py --capture` lets each user save the 11 states once, in about two minutes, each checked automatically. Clause 10 forbids training AI on the sounds. Rendering is unaffected.
- **Built.** `studio.py`, `orchestra.py`, `setup.py` with 1.2 GB of open samples, `listen.py`. The Strudel skill left main and stays under tag `v1.1.0`.

### 9. Extended search for better open libraries (2026-10-22 to 23)

- **Ask.** « J'ai peur qu'on soit limité quand même un peu par l'aspect fermé et limité de la banque gratuite de Spitfire. »
- **Found.** Nothing open matches Discover for string sections or choir. Candidates: Sonatina Symphonic Orchestra 4.0 (CC Sampling Plus, real sections, CC1 on long notes), VCSL (CC0), University of Iowa MIS, and the 3D-MARCo impulse responses of St Paul's Hall (CC BY 3.0). OpenAIR was offline.
- **Test, 2026-10-23.** Black Flag v4, one score, four open variants plus Discover. A climax montage played bars 29 to 37 of each, back to back, at equal loudness.

| Variant | Intro | Theme | Break | Climax | End | Width |
|---|---|---|---|---|---|---|
| VSCO + Dragonfly | -22.2 | -16.6 | -22.4 | -11.9 | -11.3 | 0.40 |
| Sonatina + Dragonfly | -23.5 | -16.8 | -20.2 | -11.5 | -13.3 | 0.47 |
| VSCO + real hall | -22.4 | -16.7 | -22.8 | -12.1 | -10.9 | 0.30 |
| Sonatina + real hall | -23.0 | -16.6 | -20.8 | -11.6 | -13.4 | 0.37 |
| Discover | -20.4 | -15.3 | -21.1 | -12.4 | -12.0 | 0.56 |

- **Measured.** All five follow the same arc. Sonatina is darker: about 2 % of energy in high and air, against 5 % for VSCO. The real hall used a Decca tree plus rear mics. It gave a hollow width of 0.91 until its side signal was scaled by 0.6.
- **Verdict.** « la meilleure version est sans doute la deuxième », Sonatina with Dragonfly. « Mis à part, bien sûr, la dernière, qui est bien meilleure que les autres et qui est celle de Discover ».
- **Decision.** Sonatina with Dragonfly becomes the open default. The real hall added nothing and was dropped, which also saves a 740 MB download.

### 10. Choirs (2026-10-23)

- **Verdict that opened it.** Every open variant carried a sampled choir, VPO or Sonatina's chorus: « les voix ça passe pas du tout, ça fait très synthétique en fait. Et ça ruine le morceau. »
- **Diagnosis.**
  - Samples: old looped multisamples, one vowel, few dynamic layers, no legato.
  - Writing: the choir sang the fast theme note by note on "ah", re-attacked like an organ.
  - Mix: the male choir sat as loud as the horns.
- **Search.** No free choir library has vowels and legato. LABS Choir is free but plays evolving textures only, with Discover's friction. Commercial choirs (Aurora, Strezov, 8Dio) are paid and need Kontakt.
- **Decision.** No sampled choir in open mode. Test singing synthesis.

### 11. DiffSinger choir and BigVGAN (2026-10-23)

- **Hypothesis.** A singing-voice model driven note by note is the only open way to get syllables, legato and expression.
- **Built.** `sing.py` reads OpenUtau's DiffSinger voicebanks (ONNX) without OpenUtau.
  - Inputs: phonemes and durations, then a pitch curve drawn from the score with 40 ms glides, a vibrato that grows in, and a slow drift.
  - Voices that allow commercial use: Hoshino Hanami ~AI❤dol~ by LotteV for the upper sections, with credit required, whose soft and powerful timbres are blended along CC1; Namine Ritsu by Canon for the lower ones.
  - SATB. Each singer has their own timing (about ±15 ms), tuning (about ±7 cents), vibrato, formant and timbre.
  - Writing: held chords on do-mi-ne, be-ni-te, mi-se-re, ru-mi-na, in bars 29 to 44, 7 to 9 dB below the horns.
- **Measured.** Pitch within 1 % of the target. The first test used 4 singers per section, 16 voices, and added 4 min 30 to each render.
- **Verdict.** « C'est pas mal du tout, hein, franchement. Ça fait un peu synthétique, mais je pense qu'on peut pousser. »
- **Blocker.** The community vocoders (OpenVPI NSF-HiFiGAN and PC-NSF-HiFiGAN, AI❤dolGAN) are CC BY-NC-SA 4.0, so non-commercial.
- **Fix.** NVIDIA BigVGAN v2, 44 kHz, 128 bands, MIT.
  - DiffSinger's mels cover 40 Hz to 16 kHz. Each frame is mapped back to a linear spectrum, then onto BigVGAN's full-band mels. Pitch and level stay the same.
  - PyTorch on CPU: 12 s per 4.7 s of audio.
  - The ONNX export needed two workarounds: edge padding rewritten as a concat, and channel counts frozen.
  - onnxruntime-directml on the GPU: 0.7 s per 4.7 s.
- **Shipped as v2.1.0.** Six singers per section, 24 voices. Black Flag v5 renders in 2 min 15. A fresh install takes 7.5 min and fetches only the Sonatina samples the patches use (220 MB). That install test caught 55 brass staccato samples that were being skipped.
- **Verdict on v5.** « Est pas mal à priori ».

### 12. The rebuild decision (2026-10-23)

- **Decision.** Log the research, then « repartir de zéro pour la skills », so that it covers « la dernière manière de faire, la plus ouverte, celle qui marche le mieux ».
- **Why.** Three days of leads left their residue in the repo. The skill should carry only the approach that won.
- **Kept.** Score as Python code, Sonatina by default, the sung choir with BigVGAN, Dragonfly, the ear, -14 LUFS. Discover stays an option.
- **Removed.** Virtual Playing Orchestra, VSCO's strings, brass, harp and flute with the code that turned their sample names into SFZ, sections built from detuned soloists, the 3D-MARCo hall, the sampled choirs and the library switch. VSCO is down to the five percussion sounds Sonatina lacks (57 MB instead of 960). Harp and flute now come from Sonatina, calibrated to the old levels.
- **Reorganised.** Discover's hosting, keyswitches, adaptations and capture moved to their own module. One catalog holds both modes. Every command runs with `uv run --with-requirements requirements.txt`. Setup downloads about 1.9 GB.

## Dead ends

| Approach | Why it failed | What it taught |
|---|---|---|
| Strudel alone | browser oscillators and isolated samples: « très synthétique » | the sound source was the limit, not the writing |
| ACE-Step cover at strength 0.3 to 0.5 | generic loop, form and dynamics lost | the draft carries the composition, the model only adds a skin |
| ACE-Step cover per bus | every bus darkened, piano mids 36 % to 5 %, no interplay | the model needs the whole mix |
| Strudel exported to SFZ samples, early | quantised, thin low end, judged « pas terrible » | samples need performance programming and a real orchestral source |
| Hand-written DSP mastering chain | still synthetic underneath | polish cannot fix a synthetic source |
| Cover from noise (`--source 0`) | chords rewritten, chroma 0.73 | measure harmony, not only timing |
| Cover from the draft (source 0.5 to 0.85) | the GM timbre stays | no setting gives both real sound and the score's harmony |
| Native text-to-music, ACE-Step 1.5 turbo | « pas au niveau d'une musique de film » | open generators rank 11th to 13th at best; the generator is the ceiling |
| Closed generators and cloud APIs | rejected on principle | they are the competitors, not bricks |
| REAPER, Ableton, Bitwig | paid licences | the skill must install everything itself |
| More instruments, same writing (v2) | colour unchanged | writing makes the colour |
| Discover strings and horns over VSCO | clear solo, lost in the mix | one consistent source beats a hybrid |
| Shipping Discover instrument states | EULA clauses 5 and 8 | each user captures their own once |
| Driving the Spitfire app with computer use | admin-only app, captcha, focus fights | the user does GUI steps, the skill does the rest |
| Real hall convolution (3D-MARCo) | added nothing, width 0.91 before correction | with these samples the room is not the bottleneck |
| Sampled choirs (VPO, Sonatina) | « ça ruine le morceau » | choirs need syllables and legato, held writing, a lower level |
| DiffSinger community vocoders | CC BY-NC-SA | check the licence of every link in a model chain |
| Magenta RealTime 2 driven by MIDI | MIDI control exists only in a macOS engine | untestable on the target machine |
| P-MUSE, Break-the-Beat, JASCO, YuE2 | no weights, or non-commercial, or 24 GB | research demos are not bricks |

## Lessons that still hold

**The writing makes the colour.**
- v2 added parts and kept the colour. v3 changed only the writing and earned « correctes ».
- What worked: a short motif with a strong interval, octaves and open fifths, a real floor, a stop before the climax.
- Energy below 60 Hz went from 0.8 % to 14.8 % through writing alone.

**The recordings set the ceiling.**
- The same v3 score on Discover was « bien meilleur que tout ce qu'on a fait avant ».
- Sonatina beat VSCO on the same score, and both stayed far below Discover.
- No mix setting, room or extra layer closed that gap.

**Metrics never rank renders. Only his ear decides.**
- In the bake-off, the flag-free renders with the best mids lost to a render flagged `muddy`.
- He picked seed 777, the take the ear ranked lowest on arc fidelity.
- The ear exists to catch defects and explain what he heard, never to pre-select.

**Present every variant, at equal loudness.**
- Takes were delivered at -14 LUFS, never filtered by metrics.
- The climax montage put 9 s of each render back to back at the same loudness. It turned a five-way comparison into one listen.

**Measure what the process might break.**
- Onset F1 showed that ACE-Step keeps timing.
- Bar levels showed that it flattens dynamics.
- Chroma showed that it rewrites harmony.
- Pitch error showed that the sung choir is in tune within 1 %.

**Verify the renderer before judging the music.**
- Strudel's node pool caused random 2 to 18 dB holes that sounded like mixing problems.
- The fresh-install test of v2.1.0 caught 55 missing brass samples.

**Claude cannot hear.**
- As of October 2026 the API takes no audio input.
- The ear turns a render into numbers and a spectrogram, and the user listens.
- The skill reports what it measured and never claims a track sounds great.

**Friction kills.**
- Discover's quality came with an account, a captcha, an admin-only app and 11 GUI windows.
- The answer was an open mode that installs alone, plus a one-time capture of about two minutes for Discover.

**Licences decide what ships.**
- Every brick was checked: ACE-Step weights MIT, Strudel AGPL loaded from a CDN, Spitfire's EULA, DiffSinger's vocoders, Sonatina's CC Sampling Plus, 3D-MARCo's CC BY 3.0.
- One non-commercial vocoder was enough to block the choir until BigVGAN replaced it.
- Hanami's licence requires a credit, which the skill tells the user.

**Keep contrast alive in the mix.**
- A hard bus compressor erased the climax.
- The gentle default glue is -14 dB at 2:1, with the climax 3 to 5 LUFS above the theme.

## Open questions and next leads

**Choir realism.**
- The sung choir is still « un peu synthétique ».
- Leads: more singers or voices per section, breaths, consonant timing, voicebanks with Latin or English phonemes instead of romaji syllables.

**More open voices.**
- Only two voicebanks with commercial-use licences are in use.
- Variety within a section comes mostly from Hanami's three timbres.

**Speed outside Windows.**
- DirectML runs only on Windows. Elsewhere BigVGAN falls back to the CPU, about 2.5 times slower than real time.
- CUDA and CoreML execution providers are untested.

**Platforms.**
- macOS and Linux were never tested end to end: sfizz and Dragonfly come from package managers or release pages there.

**Open orchestral sound.**
- Sonatina is darker than VSCO. Correcting it at the mix is untested.
- Leads: VCSL (CC0) for more percussion layers and round robins, University of Iowa MIS for anechoic solo brass and winds to layer into sections.
- Neural instruments are where the field is going. Dreamtonics Instrument X is paid. Open DDSP and TokenSynth are not at that level yet.

**Discover.**
- The capture step stays manual and GUI-only.
- Rendering with Discover takes about 4 min 20 for a 1-minute cue because of plugin warm-up.
- Spitfire's LABS is moving to Splice. Its terms should be watched.

**Beyond orchestral.**
- Surge XT is installed and checked, but no track has used it.
- The multi-style proof planned for v1 (lo-fi, techno, ambient, cinematic) was never done in the studio.

**Tooling.**
- A reference-based check, comparing a mix to a track the user supplies, is still an idea. Matchering is available.
- Whether an MCP wrapper is worth it was deferred. The command line is already the lowest level.
- A blind listening test, open since spec 001, would turn his verdicts into an argument others can check.
