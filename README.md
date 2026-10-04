# Sawtak Arabi Skill

Arabic voiceovers for Claude Code and Codex, powered by [Sawtak Arabi](https://sawtakarabi.ai). Choose a voice, generate narration, and add it to your video workflow.

## Install

Requires Node.js/npm for the installer and Python 3.10+ for generation.

```bash
npx skills add SawtakArabi/skill --skill arabic-voiceover -g -a claude-code -a codex
```

## Setup

Create an API key in your [Sawtak dashboard](https://sawtakarabi.ai), then set `SAWTAK_API_KEY` in your agent’s environment. Speech generation uses your Sawtak balance.

Install the Python packages in [requirements.txt](skills/arabic-voiceover/requirements.txt). Your agent can do this when setting up the skill.

To check setup without generating audio, ask your agent to run the skill’s `doctor` command.

## Usage

Ask your agent:

> اعمل فيديو إعلان ٣٠ ثانية باللهجة المصرية مع فويس أوفر.

Or invoke the skill directly with `/arabic-voiceover` in Claude Code or `$arabic-voiceover` in Codex.

The skill generates WAV audio and reports its duration for timing your video. See [SKILL.md](skills/arabic-voiceover/SKILL.md) for the workflow and CLI commands.

## License

[MIT](LICENSE)
