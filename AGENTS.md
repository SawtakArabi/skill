# Maintaining Sawtak Skills

This public repository contains portable agent skills for Sawtak Arabi. Keep the
skill self-contained under `skills/arabic-voiceover`. Reuse the official OpenAI
Python SDK and standard Agent Skills packaging. Do not create another SDK,
installer, speech engine, or video renderer.

- The speech helper connects to Sawtak, not OpenAI. Keep automatic paid-request
  retries disabled. Do not overwrite completed audio or metadata. Save identifiers
  and settings beside the output; interrupted audio stays explicitly partial.
  Operation inspection reads status/billing only, never recovers or regenerates audio.
- Never commit keys, private account metadata, generated media, or environments.
- Keep `scripts/package.py`'s file allowlist current when adding skill resources.
- Run `python3 -m pytest tests -q` after client changes and build the ZIP with
  `python3 scripts/package.py`. Run these manually; no CI test workflow is needed.
- Test live synthesis only with an authorized account and small script. Keep
  generated media on the user's designated processing host when one is specified.
- Distinguish SDK/mock tests, live API tests, listening checks, automatic agent
  selection, and hosted Claude execution. Do not claim one establishes another.

- `references/dialects.json` reuses platform `frontend/scripts/shipped-voices.json`
  labels, with skill aliases; it is a snapshot, not live voice availability. Include
  it in the ZIP. Preserve pagination in compact voice output.
- `doctor` must work with missing SDK dependencies and credentials, never synthesize,
  and never print API keys, account details, or raw import diagnostics.

- Missing-key guidance must link directly to dashboard API Keys, name the Create key
  and Copy actions, explain environment inheritance, and resume the original task.
  No key means connectivity is untested, not that all other setup checks passed.
