#!/usr/bin/env python3
"""Sawtak voice discovery and narration using the official OpenAI Python SDK."""

import argparse
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
from urllib.parse import quote, urlencode, urlparse
import uuid
import wave

try:
    import httpx
    from openai import APIConnectionError, APIStatusError, OpenAI
except ModuleNotFoundError:
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    raise SystemExit(
        "Missing Python dependencies. Install them in your Python environment:\n"
        f"{shlex.quote(sys.executable)} -m pip install -r {shlex.quote(str(requirements))}"
    ) from None


BASE_URL = "https://api.sawtakarabi.ai/v1"
SAMPLE_RATE = 24000


def make_client():
    key = os.environ.get("SAWTAK_API_KEY", "").strip()
    if not key:
        raise ValueError("Create an API key in your Sawtak dashboard and set SAWTAK_API_KEY in your environment.")
    base = os.environ.get("SAWTAK_API_BASE_URL", BASE_URL).rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("SAWTAK_API_BASE_URL must be an HTTPS API URL without credentials, query, or fragment.")
    return OpenAI(api_key=key, base_url=base, max_retries=0, timeout=180.0)


def list_voices(client, args):
    query = {"limit": args.limit, "sort": "most_liked"}
    for name in ("dialect", "gender", "search", "after"):
        value = getattr(args, name)
        if value:
            query[name] = value
    # Sawtak expects repeated dialect= values, not the SDK's dialect[]= convention.
    return client.get("/voices?" + urlencode(query, doseq=True), cast_to=object)


def generate(client, args):
    text = args.text_file.read_text(encoding="utf-8")
    if not text.strip() or len(text) > 10000 or any(len(word) > 400 for word in text.split()):
        raise ValueError("Use 1–10000 characters, with words no longer than 400 characters; split long scripts into scenes.")
    output = args.output.expanduser().absolute()
    if output.suffix.lower() != ".wav":
        raise ValueError("Output must have a .wav extension.")
    partial = output.with_suffix(".partial.wav")
    metadata_path = output.with_suffix(".json")
    for path in (output, partial, metadata_path):
        if path.exists() or path.is_symlink():
            raise ValueError(f"Output already exists: {path}. Reuse it or choose a new filename.")
    key = args.idempotency_key or str(uuid.uuid4())
    if not 1 <= len(key) <= 128 or any(ord(c) < 33 or ord(c) > 126 for c in key):
        raise ValueError("Idempotency key must be 1–128 printable ASCII characters without spaces.")
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "idempotency_key": key, "operation_id": None,
        "voice": args.voice, "path": str(output), "partial_path": None,
        "state": "started", "characters": len(text),
        "settings": {"model": "arabic-tts-1", "response_format": "pcm",
                     "sample_rate": SAMPLE_RATE, "enhance_pronunciation": args.enhance_pronunciation},
    }
    # Exclusive creation also prevents two invocations from claiming the same output.
    with metadata_path.open("x", encoding="utf-8") as record:
        json.dump(metadata, record, ensure_ascii=False, indent=2)

    def save(event):
        fd, name = tempfile.mkstemp(dir=output.parent, prefix=".generation-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as record:
                json.dump(metadata, record, ensure_ascii=False, indent=2)
            os.replace(name, metadata_path)
        finally:
            Path(name).unlink(missing_ok=True)
        print(json.dumps({"event": event, **metadata}), file=sys.stderr, flush=True)

    save("generation_started")
    total = 0
    pending = b""
    owns_partial = False
    try:
        raw = partial.open("xb")
        owns_partial = True
        with raw, wave.open(raw, "wb") as wav:
            wav.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
            with client.audio.speech.with_streaming_response.create(
                model="arabic-tts-1", voice=args.voice, input=text,
                response_format="pcm",
                extra_body={"sample_rate": SAMPLE_RATE, "enhance_pronunciation": args.enhance_pronunciation},
                extra_headers={"Idempotency-Key": key},
            ) as response:
                metadata["operation_id"] = response.headers.get("x-request-id")
                metadata["state"] = "streaming"
                save("generation_headers")
                content_type = response.headers.get("content-type", "").split(";")[0]
                if content_type != "audio/pcm":
                    raise ValueError(f"Expected audio/pcm, received {content_type!r}; no audio saved.")
                rate = response.headers.get("x-sample-rate")
                if rate is not None and rate != str(SAMPLE_RATE):
                    raise ValueError("Unexpected sample rate; no audio saved.")
                for chunk in response.iter_bytes():
                    pending += chunk
                    size = len(pending) - len(pending) % 2
                    if size:
                        wav.writeframes(pending[:size])
                        raw.flush()
                        total += size
                        pending = pending[size:]
            if not total or pending:
                raise ValueError("Empty or incomplete PCM response. Do not automatically generate again.")
        # Only a completed stream becomes the requested file; never overwrite audio.
        os.link(partial, output)
    except (Exception, KeyboardInterrupt) as exc:
        if isinstance(exc, APIStatusError):
            # Only a duplicate response identifies an existing operation. Other error
            # request IDs may be tracing IDs, not operation IDs.
            body = exc.body if isinstance(exc.body, dict) else {}
            if exc.status_code == 409 and body.get("operation_id"):
                metadata["operation_id"] = body["operation_id"]
            metadata["http_status"] = exc.status_code
        metadata["state"] = "incomplete" if total else "unknown"
        metadata["partial_path"] = str(partial) if total else None
        metadata["duration_seconds"] = total / (SAMPLE_RATE * 2)
        if not total and owns_partial:
            partial.unlink(missing_ok=True)
        save("generation_incomplete")
        raise
    partial.unlink()
    metadata.update(state="completed", duration_seconds=total / (SAMPLE_RATE * 2))
    save("generation_completed")
    return {**metadata, "metadata_path": str(metadata_path), "sample_rate": SAMPLE_RATE, "channels": 1}


def inspect_operation(client, args):
    try:
        return client.get("/operations/" + quote(args.operation_id, safe=""), cast_to=object)
    except APIStatusError as exc:
        if exc.status_code != 404:
            raise
        return {"id": args.operation_id, "state": "unknown",
                "hint": "Operation not found. This does not prove failure or authorize another generation."}


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest="command", required=True)
    voices = sub.add_parser("voices", help="List voices; follow next_cursor with --after")
    voices.add_argument("--dialect", action="append", help="Exact catalog dialect label; repeat to include several")
    voices.add_argument("--gender", choices=["male", "female", "neutral"])
    voices.add_argument("--search", help="Search voice names (not dialect names)")
    voices.add_argument("--limit", type=int, default=25, choices=range(1, 101), metavar="1..100")
    voices.add_argument("--after", help="Opaque next_cursor from the previous page")
    speech = sub.add_parser("generate", help="Generate narration; consumes Sawtak credits")
    speech.add_argument("--voice", required=True, help="Ready voice ID from the catalog")
    speech.add_argument("--text-file", type=Path, required=True, help="UTF-8 narration script")
    speech.add_argument("--output", type=Path, required=True, help="New WAV path; existing files are never overwritten")
    speech.add_argument("--idempotency-key", "--request-id", dest="idempotency_key", help="Optional duplicate-protection key; managed automatically if omitted")
    speech.add_argument("--enhance-pronunciation", action="store_true", help="Opt into Sawtak tashkeel; off by default")
    inspect = sub.add_parser("inspect", help="Check operation status and billing; does not generate or download audio")
    inspect.add_argument("operation_id", help="Operation ID from saved metadata")
    return cli


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        with make_client() as client:
            result = {"voices": list_voices, "generate": generate, "inspect": inspect_operation}[args.command](client, args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except APIStatusError as exc:
        body = exc.body if isinstance(exc.body, dict) else {}
        error = body.get("error", body)
        code = error.get("code", "api_error") if isinstance(error, dict) else "api_error"
        hints = {
            401: "Check SAWTAK_API_KEY.", 403: "Access denied. Check your API key in the Sawtak dashboard.",
            402: "Check your Sawtak balance.", 409: "This request ID was already used. Audio is not replayed; do not automatically generate again.",
            429: "Rate limited; no automatic retry was made.", 503: "Service unavailable; no automatic retry was made.",
        }
        print(json.dumps({"error": code, "status": exc.status_code, "server_request_id": exc.request_id,
                          "hint": hints.get(exc.status_code, "API audio cannot be retrieved later. Do not automatically generate again.")}), file=sys.stderr)
    except (APIConnectionError, httpx.TransportError):
        print("Connection or stream interrupted. No automatic retry was made. The outcome is uncertain and API audio cannot be retrieved later. Ask before another paid generation.", file=sys.stderr)
    except KeyboardInterrupt:
        print("Interrupted. Check saved metadata and any partial audio before another generation.", file=sys.stderr)
        return 130
    except (OSError, ValueError, wave.Error) as exc:
        print(str(exc), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
