# Sawtak Arabi Skill

Arabic voiceovers for Claude Code and Codex, powered by [Sawtak Arabi](https://sawtakarabi.ai). Choose a voice, generate narration, and add it to your video workflow.

## Install

```bash
npx skills add SawtakArabi/skill --skill arabic-voiceover -g -a claude-code -a codex
```

## Setup

Create a [Sawtak API key](https://sawtakarabi.ai) with `tts` and `voices` access, then set `SAWTAK_API_KEY` in your agent’s environment. Speech generation uses your Sawtak balance.

Requires Python 3.10+ and the packages in [requirements.txt](skills/arabic-voiceover/requirements.txt). Your agent can install these when setting up the skill.

## Usage

Ask your agent:

> اعمل فيديو إعلان ٣٠ ثانية باللهجة المصرية مع فويس أوفر.

Or invoke the skill directly with `/arabic-voiceover` in Claude Code or `$arabic-voiceover` in Codex.

The skill generates WAV audio and reports its duration for timing your video. See [SKILL.md](skills/arabic-voiceover/SKILL.md) for the workflow and CLI commands.

## Claude chat and Cowork

[Download the skill ZIP](https://github.com/SawtakArabi/skill/releases/latest/download/arabic-voiceover.zip) and upload it through **Customize → Skills**. Hosted execution is experimental and requires Python dependencies, API connectivity, and secure credential configuration.

## License

[MIT](LICENSE)
