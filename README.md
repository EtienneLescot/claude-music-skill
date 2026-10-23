# claude-music-skill

**Your coding agent composes, orchestrates and mixes. A real sampled orchestra plays it.**

An [Agent Skill](https://agentskills.io) that turns a one-line request into a finished instrumental track, film and orchestral first. The agent works the way a composer does with a virtual orchestra, and the way an agent drives Blender rather than a model that outputs a picture:

- **It writes the score as code**: every note, articulation, swell and fader move, in a Python file you can read and edit.
- **Real recordings play it**: sampled strings, brass and percussion, and a choir sung by singing-voice models, rendered from the command line, mixed in a hall and mastered to -14 LUFS.
- **An ear checks it**: the agent cannot hear, so the render is measured section by section and drawn as a spectrogram it reads.

No GPU, no cloud music service. Works with any agent that reads `SKILL.md`, runs shell commands and opens an image: Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode…

## Two sound sources

| | Open (default) | BBC Symphony Orchestra Discover |
|---|---|---|
| What plays | [Sonatina Symphonic Orchestra](https://github.com/peastman/sso) (CC Sampling Plus), [VSCO 2 Community Edition](https://github.com/sgossner/VSCO-2-CE) (CC0) and [Virtual Playing Orchestra](http://virtualplaying.com/virtual-playing-orchestra/) (free), through [sfizz](https://sfz.tools/sfizz/) | [Spitfire Audio's free orchestra](https://www.spitfireaudio.com/products/bbc-symphony-orchestra-discover): real sections recorded together at Maida Vale, one hall |
| Setup | automatic, no account | you get it free with a Spitfire account, then a 2-minute capture |
| Sound | a good mockup | clearly better |

The same score renders in both: the skill picks Discover when it is installed.

## How it works

```mermaid
flowchart LR
    A["Request<br/>« la musique de pirate,<br/>des Caraïbes »"] --> B["Brief<br/>form, tempo, key,<br/>orchestration, energy"]
    B --> C["Score<br/>Python: notes,<br/>articulations, swells"]
    C --> D["Studio<br/>sampled orchestra,<br/>hall, mastering"]
    D --> E["Ear<br/>loudness per section,<br/>spectrogram, stems"]
    E -- fix --> C
    E --> F["Track, stems, score"]
```

The details, and the listening tests behind each choice, are in [docs/how-it-works.md](docs/how-it-works.md).

## Install

**Any agent.** Copy the skill folder into your agent's skills folder (many read `.agents/skills/` or `~/.agents/skills/`; Claude Code reads `~/.claude/skills/`):

```bash
git clone https://github.com/EtienneLescot/claude-music-skill
cp -r claude-music-skill/skills/music-studio ~/.agents/skills/
```

**Claude Code**, as a plugin:

```
/plugin install music-skill --marketplace EtienneLescot/claude-music-skill
```

The first time you ask for music, the agent runs the setup, asking you first: sfizz, Dragonfly Reverb, the samples and the choir's voices, about 3 GB, into `~/.music-studio` (or `STUDIO_HOME`). Nothing is installed system-wide. For Discover, see [docs/install.md](docs/install.md).

## Requirements

| | |
|---|---|
| Agent | reads `SKILL.md`, runs shell commands, opens images |
| Tools | [uv](https://docs.astral.sh/uv/) |
| Disk | about 1.3 GB; 240 MB more for Discover |
| System | Windows tested. macOS and Linux: install `sfizz` from your package manager if setup finds no `sfizz_render` |

## What goes over the network

Nothing you compose leaves your machine. Setup downloads sfizz and Dragonfly Reverb from their GitHub releases, the samples from the Sonatina, VSCO 2 CE and Virtual Playing Orchestra GitHub repositories, the choir's two voices from their authors' pages and the BigVGAN vocoder from NVIDIA on Hugging Face. Discover comes from Spitfire, through their app, if you choose it.

## Docs

- [How it works](docs/how-it-works.md): the studio, the two sources, the ear, what the listening tests taught
- [Install](docs/install.md): setup, Discover step by step, platforms
- [Troubleshooting](docs/troubleshooting.md)

## Status

Tested on Windows on orchestral and film music. Electronic styles are the next step. The first version of this skill (Strudel code performed by ACE-Step 1.5) is kept under the tag [v1.1.0](https://github.com/EtienneLescot/claude-music-skill/tree/v1.1.0).

## Licence

MIT, see [LICENSE](LICENSE). The music you make is yours. Sonatina Symphonic Orchestra is CC Sampling Plus, VSCO 2 CE CC0, Virtual Playing Orchestra free for any use, sfizz BSD-2, Dragonfly Reverb and DawDreamer GPL-3, BigVGAN MIT; the choir's voices allow commercial use (Namine Ritsu by Canon; Hoshino Hanami ~AI❤dol~ by LotteV, with credit). All are downloaded from their sources, not redistributed here. BBC Symphony Orchestra Discover follows Spitfire's terms: music made with it can be released commercially, royalty free; its sounds and patches may not be redistributed or used to train AI, which is why this project ships no Discover data.
