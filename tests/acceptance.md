# Manual acceptance scenarios

Run in clean agent sessions with only this skill installed and a usable Sawtak account. Use a scratch video project and a small generation budget. Never log keys.

| Scenario | Prompt | Expected observable result |
| --- | --- | --- |
| Implicit Arabic | اعمل فيديو إعلان ٣٠ ثانية باللهجة المصرية مع فويس أوفر | Loads skill, selects a ready Egyptian voice, generates audio, integrates it into a video, checks the ending |
| Implicit English | Add Arabic narration to this product video for a Saudi audience | Loads skill, selects a relevant catalog voice, preserves the requested audience |
| Explicit | Use arabic-voiceover to narrate this short Arabic script | Generates playable WAV and reports measured duration |
| Negative: silent | Create a silent Arabic title animation | No Sawtak call |
| Negative: captions | Add Arabic subtitles without changing the audio | No Sawtak call |
| Negative: provider | Use Microsoft's Hamed voice for this Arabic video | Does not substitute Sawtak |
| Missing key | Narrate this Arabic script, with no key configured | Explains setup; no invented audio or provider fallback |
| Interrupted request | Interrupt a speech response | No finalized partial WAV, no automatic second charge attempt |
| Repeat scene | Re-run with a completed scene's output path | Preserves audio and makes no synthesis request |

Record host/version, whether discovery occurred, voice ID/dialect, request ID, audio duration, final video duration, and listening observations. Never call a structural WAV check a pronunciation review. Test both Claude Code and Codex; ZIP import/hosted execution is a separate check.
