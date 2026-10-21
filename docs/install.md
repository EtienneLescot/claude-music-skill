# Install

The agent sets everything up on first use, after asking you. To do it by hand:

## 1. The skill

Copy `skills/strudel-composer/` into your agent's skills folder:

| Agent | User folder | Project folder |
|---|---|---|
| Many agents (shared location) | `~/.agents/skills/` | `.agents/skills/` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Cursor | | `.cursor/skills/` |
| GitHub Copilot | `~/.copilot/skills/` | `.github/skills/` |
| Gemini CLI | | `.gemini/skills/` |
| OpenCode | `~/.config/opencode/skills/` | `.opencode/skills/` |

These paths change between releases: check your agent's documentation. In Claude Code you can install the plugin instead:

```
/plugin install music-skill --marketplace EtienneLescot/claude-music-skill
```

On Claude Code older than 2.1.275, use two steps: `/plugin marketplace add EtienneLescot/claude-music-skill`, then `/plugin install music-skill@claude-music-skill`.

## 2. The ear

```bash
uv run --with playwright==1.63.0 python -m playwright install chromium
```

Set `PLAYWRIGHT_BROWSERS_PATH` first to put Chromium on another disk.

## 3. The performer: ACE-Step 1.5

About 10 GB with its models. To keep them off the system disk, set `UV_CACHE_DIR` and `HF_HOME` to a larger disk before installing.

```bash
git clone https://github.com/ace-step/ACE-Step-1.5 /path/to/ACE-Step-1.5
cd /path/to/ACE-Step-1.5
git checkout ca1e85fe9430179831e6bc6be790c332190a3866   # the commit this skill was tested with
uv sync
export ACESTEP_DIR=/path/to/ACE-Step-1.5
```

That is the standard install, for NVIDIA (CUDA) and Apple Silicon (MLX). For AMD (ROCm) and Intel (XPU), follow ACE-Step's [installation guide](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INSTALL.md): they use their own Python environment, and `perform.py` then runs with that environment's Python.

On Windows PowerShell, set variables with `$env:ACESTEP_DIR = 'E:\ACE-Step-1.5'`.

## 4. Check

From the folder that holds the skill:

```bash
uv run --project "$ACESTEP_DIR" python perform.py --check
```

prints `check ok`: the loudness meter matches the BS.1770 reference signals, the dynamics transfer and the limiter work. The models download from Hugging Face on the first performance.
