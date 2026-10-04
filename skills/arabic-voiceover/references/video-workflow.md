# Narration in a video

Use the user's existing video project and rendering tools. This skill supplies narration; it does not choose or install a new video engine.

1. Generate each narration scene before finalizing its visual timing. Use the returned `duration_seconds`, not an estimated Arabic words-per-minute figure.
2. Place scenes in order, keeping the same speaker voice. Reuse completed clips after an interrupted run. In frame-based projects, round each audio duration up to whole frames at the project's frame rate.
3. For a fixed 30-second brief, reserve time for pauses and transitions. If narration exceeds the budget, revise the script with the user's intent preserved and regenerate only changed scenes. Do not cut off speech or aggressively speed it up to force a fit.
4. Add the WAV to the existing timeline (for example, the existing Remotion audio component or Blender sound strip). Keep narration audible over background music. Do not replace existing soundtrack audio unless requested.
5. If FFmpeg is already the project's tool and the silent visual track is at least as long as narration, a basic mux is:

   ```bash
   ffmpeg -n -i visuals.mp4 -i narration.wav \
     -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -movflags +faststart final.mp4
   ```

   This example selects narration as the only audio track. For an existing soundtrack, mix within the project's editor instead. Avoid `-shortest` as a shortcut: it can truncate the intended ending. Extend visuals deliberately if needed.
6. Inspect final video and audio stream durations and play the beginning, scene transitions, and ending. Confirm no narration is clipped. A successful render command alone is insufficient.

The speech API does not provide word-level alignment. Do not present estimated subtitle timings as measured timestamps. Use existing alignment tooling if precise captions are requested and available.
