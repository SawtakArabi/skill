# Arabic Voiceover by Sawtak

Give Claude Code and Codex Arabic narration for videos, reels, ads, and presentations using [Sawtak Arabi](https://sawtakarabi.ai).

> اعمل فيديو إعلان ٣٠ ثانية باللهجة المصرية مع فويس أوفر.

The skill helps your agent select an available voice, generate narration, measure its duration, and add it to your existing video workflow. **Installation is free. Speech generation uses your Sawtak account balance.** It requires a Sawtak API key; it does not include a local speech model or a video renderer.

## Install

Use the existing [Vercel Skills CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add SawtakArabi/sawtak-skills --skill arabic-voiceover -g -a claude-code -a codex
```

Or clone this repository and copy `skills/arabic-voiceover` to:

- Claude Code: `~/.claude/skills/arabic-voiceover`
- Codex: `~/.agents/skills/arabic-voiceover`

Start a new agent session after installation. The agent can select the skill when an Arabic narration request matches its description; selection is not guaranteed for every prompt. Invoke explicitly with `/arabic-voiceover` in Claude Code or `$arabic-voiceover` in Codex if needed.

## Connect Sawtak

1. Create an account and API key at [sawtakarabi.ai](https://sawtakarabi.ai), with `tts` and `voices` scopes and sufficient balance.
2. Configure `SAWTAK_API_KEY` in the environment that launches your agent. Keep the key out of chat, source files, and Git. For an interactive Bash terminal, a hidden prompt avoids putting the key in shell history:

   ```bash
   read -rsp 'Sawtak API key: ' SAWTAK_API_KEY
   export SAWTAK_API_KEY
   ```

   For Zsh, use `read -rs 'SAWTAK_API_KEY?Sawtak API key: '` followed by `export SAWTAK_API_KEY`. Desktop apps may not inherit a terminal's environment; use that host's credential configuration or launch the CLI from the configured terminal.
3. Use Python 3.10+ with the dependencies in the installed skill's `requirements.txt`. From a clone, for example:

   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install -r skills/arabic-voiceover/requirements.txt
   .venv/bin/python skills/arabic-voiceover/scripts/generate.py voices --limit 10
   ```

The API URL defaults to `https://api.sawtakarabi.ai/v1`. Only set `SAWTAK_API_BASE_URL` when you deliberately use another trusted Sawtak environment.

## Use it

Try either:

> Add Egyptian Arabic narration to this video. Use a suitable available Sawtak voice and fit the scenes to the spoken audio.

> استخدم arabic-voiceover وحوّل النص ده لفويس أوفر باللهجة المصرية، واحفظه WAV.

The agent must have a working video tool to finish a video. This package integrates with that workflow rather than installing its own renderer. It preserves explicit choices of another speech provider and should not activate for silent videos or subtitles alone.

For direct use, save the script as UTF-8 and select a ready voice ID from the catalog:

```bash
.venv/bin/python skills/arabic-voiceover/scripts/generate.py generate \
  --voice YOUR_VOICE_ID --text-file narration.txt --output narration.wav
```

The command returns JSON with the path, measured duration, voice, and request identifiers. Existing files are protected. Generation is never automatically retried. After an interrupted request, check Sawtak generation history before starting another paid request. Reusing a request ID returns a duplicate response, not the original audio.

## Claude chat and Cowork

Download [arabic-voiceover.zip](https://github.com/SawtakArabi/sawtak-skills/releases/latest/download/arabic-voiceover.zip) and upload it through **Customize → Skills**. The ZIP has the same skill used by the coding agents.

**Hosted execution is not yet verified.** The host must provide Python dependencies, access to `api.sawtakarabi.ai`, and secure API-key configuration. ZIP installation alone does not provide these. If the host cannot supply them, use Claude Code or Codex with the local setup above. Do not paste an API key into a conversation as a workaround.

## What is reused

- [Agent Skills](https://agentskills.io): standard `SKILL.md` packaging and discovery.
- [OpenAI Python SDK](https://github.com/openai/openai-python): the actual speech streaming client and authenticated custom-endpoint requests, pointed at Sawtak. No OpenAI account or key is needed.
- Python standard library `wave`: finalized WAV output and sample-based duration; no custom audio codec.
- [Vercel Skills CLI](https://github.com/vercel-labs/skills): installation into agent skill directories; no custom installer.

## Development and verification

```bash
python3 -m pip install -r skills/arabic-voiceover/requirements.txt pytest
python3 -m pytest tests -q
python3 scripts/package.py
```

The tests use the real SDK with HTTPX mock transport to verify Arabic input, catalog pagination, WAV output, interruption handling, no automatic retry, and overwrite protection. They do not establish voice quality or automatic agent activation. See [the manual acceptance scenarios](tests/acceptance.md) for those checks.

The packaging command creates `dist/arabic-voiceover.zip` with an explicit file allowlist, excluding credentials, caches, generated audio, and test files.

Verified on 2026-10-04: 15 tests passed with OpenAI Python SDK 2.54.0;
authenticated live voice discovery and synthesis produced a 3.84-second, 24 kHz
mono WAV from a 55-character Egyptian Arabic script. FFmpeg muxed it into a
4-second test video, and FFprobe confirmed the complete 3.84-second audio track.
This was a structural integration check, not a pronunciation review or a test of
automatic selection inside fresh Claude/Codex sessions. Hosted Claude execution
remains unverified.

## License

MIT for this skill and helper code. The license does not grant free Sawtak API usage or rights to third-party voices/content. Dependencies retain their own licenses.
