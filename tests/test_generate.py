import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import wave

import httpx
from openai import OpenAI
import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/arabic-voiceover/scripts/generate.py"
spec = importlib.util.spec_from_file_location("generate", SCRIPT)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


@pytest.fixture
def args(tmp_path):
    text = tmp_path / "scene.txt"
    text.write_text("أهلاً بيك في صوتك عربي.", encoding="utf-8")
    return helper.parser().parse_args([
        "generate", "--voice", "voice-eg", "--text-file", str(text),
        "--output", str(tmp_path / "scene.wav"), "--request-id", "scene-1",
    ])


def client(handler):
    return OpenAI(api_key="test-only", base_url=helper.BASE_URL, max_retries=0,
                  http_client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_sdk_generates_finalized_wav_and_measured_duration(args):
    def handler(request):
        assert str(request.url) == helper.BASE_URL + "/audio/speech"
        assert request.headers["authorization"] == "Bearer test-only"
        assert request.headers["idempotency-key"] == "scene-1"
        body = json.loads(request.content)
        assert body["input"] == args.text_file.read_text(encoding="utf-8")
        assert body["voice"] == "voice-eg"
        assert body["response_format"] == "pcm"
        assert body["sample_rate"] == 24000
        assert body["enhance_pronunciation"] is False
        return httpx.Response(200, headers={"content-type": "audio/pcm", "x-request-id": "op-1"}, content=b"\x01\x00" * 24000)

    with client(handler) as sdk:
        result = helper.generate(sdk, args)
    assert result["duration_seconds"] == 1
    assert result["operation_id"] == "op-1"
    with wave.open(str(args.output)) as wav:
        assert wav.getnframes() == 24000
        assert wav.getframerate() == 24000
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2


def test_catalog_preserves_filters_and_pagination():
    args = helper.parser().parse_args(["voices", "--dialect", "eg-cairene", "--dialect", "eg-alexandrian", "--after", "opaque+cursor="])
    def handler(request):
        assert request.url.params.get_list("dialect") == ["eg-cairene", "eg-alexandrian"]
        assert request.url.params["after"] == "opaque+cursor="
        return httpx.Response(200, json={"data": [{"id": "one"}], "has_more": True, "next_cursor": "next"})
    with client(handler) as sdk:
        result = helper.list_voices(sdk, args)
    assert result["next_cursor"] == "next"


@pytest.mark.parametrize("status", [401, 402, 403, 409, 429, 503])
def test_error_is_not_retried_and_leaves_no_audio(args, monkeypatch, capsys, status):
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(status, json={"error": {"code": "test_failure", "message": "failure"}})
    monkeypatch.setattr(helper, "make_client", lambda: client(handler))
    assert helper.main(["generate", "--voice", args.voice, "--text-file", str(args.text_file), "--output", str(args.output)]) == 1
    assert len(requests) == 1
    assert not args.output.exists()
    assert not list(args.output.parent.glob("*.partial"))
    assert "test-only" not in capsys.readouterr().err


class Interrupted(httpx.SyncByteStream):
    def __iter__(self):
        yield b"\x01\x00" * 100
        raise httpx.ReadError("stream lost")


def test_interrupted_stream_preserves_partial_audio(args):
    with client(lambda r: httpx.Response(200, headers={"content-type": "audio/pcm"}, stream=Interrupted())) as sdk:
        with pytest.raises(httpx.ReadError):
            helper.generate(sdk, args)
    assert not args.output.exists()
    with wave.open(str(args.output.with_suffix(".partial.wav"))) as wav:
        assert wav.getnframes() == 100
    metadata = json.loads(args.output.with_suffix(".json").read_text())
    assert metadata["state"] == "incomplete"


@pytest.mark.parametrize("content,content_type", [(b"", "audio/pcm"), (b"x", "audio/pcm"), (b"{}", "application/json")])
def test_invalid_audio_is_not_published(args, content, content_type):
    with client(lambda r: httpx.Response(200, headers={"content-type": content_type}, content=content)) as sdk:
        with pytest.raises(ValueError):
            helper.generate(sdk, args)
    assert not args.output.exists()


def test_existing_audio_is_preserved_without_paid_request(args):
    args.output.write_bytes(b"existing recording")
    def handler(request):
        pytest.fail("Must not issue a paid request")
    with client(handler) as sdk:
        with pytest.raises(ValueError, match="already exists"):
            helper.generate(sdk, args)
    assert args.output.read_bytes() == b"existing recording"


def test_missing_key_has_actionable_error(monkeypatch, capsys):
    monkeypatch.delenv("SAWTAK_API_KEY", raising=False)
    assert helper.main(["voices"]) == 1
    assert "SAWTAK_API_KEY" in capsys.readouterr().err


def test_client_disables_sdk_retries(monkeypatch):
    monkeypatch.setenv("SAWTAK_API_KEY", "test-only")
    with helper.make_client() as sdk:
        assert sdk.max_retries == 0
        assert str(sdk.base_url) == helper.BASE_URL + "/"


def test_missing_dependencies_shows_install_command():
    result = subprocess.run([sys.executable, "-S", str(SCRIPT), "voices"], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Missing Python dependencies" in result.stderr
    assert "-m pip install -r" in result.stderr
    assert str(SCRIPT.parents[1] / "requirements.txt") in result.stderr
    assert "Traceback" not in result.stderr


def test_ids_saved_before_stream_and_status_never_resynthesizes(args, capsys):
    requests = []
    class CheckedStream(httpx.SyncByteStream):
        def __iter__(self):
            saved = json.loads(args.output.with_suffix(".json").read_text())
            assert saved["operation_id"] == "op-1"
            assert saved["idempotency_key"] == "scene-1"
            assert saved["settings"]["enhance_pronunciation"] is False
            assert "generation_headers" in capsys.readouterr().err
            yield b"\x01\x00x"
            raise httpx.ReadError("lost")
    def handler(request):
        requests.append(request.method)
        if request.method == "GET":
            assert request.url.path == "/v1/operations/op-1"
            return httpx.Response(200, json={"id": "op-1", "state": "terminal", "charged_micros": 100})
        saved = json.loads(args.output.with_suffix(".json").read_text())
        assert saved["state"] == "started"
        return httpx.Response(200, headers={"content-type": "audio/pcm", "x-request-id": "op-1"}, stream=CheckedStream())
    with client(handler) as sdk:
        with pytest.raises(httpx.ReadError):
            helper.generate(sdk, args)
        status = helper.inspect_operation(sdk, helper.parser().parse_args(["inspect", "op-1"]))
    assert requests == ["POST", "GET"]
    assert status["charged_micros"] == 100
    with wave.open(str(args.output.with_suffix(".partial.wav"))) as wav:
        assert wav.getnframes() == 1
    assert not args.output.exists()


def test_missing_operation_is_unknown():
    with client(lambda r: httpx.Response(404, json={"error": {"message": "missing"}})) as sdk:
        result = helper.inspect_operation(sdk, helper.parser().parse_args(["inspect", "missing"]))
    assert result["state"] == "unknown"


def test_metadata_prevents_reusing_failed_output(args):
    args.output.with_suffix(".json").write_text("existing metadata")
    with client(lambda r: pytest.fail("Must not generate")) as sdk:
        with pytest.raises(ValueError, match="already exists"):
            helper.generate(sdk, args)


def test_keyboard_interrupt_keeps_audio_and_ids(args):
    class Stopped(httpx.SyncByteStream):
        def __iter__(self):
            yield b"\x01\x00"
            raise KeyboardInterrupt()
    with client(lambda r: httpx.Response(200, headers={"content-type": "audio/pcm", "x-request-id": "op-stop"}, stream=Stopped())) as sdk:
        with pytest.raises(KeyboardInterrupt):
            helper.generate(sdk, args)
    saved = json.loads(args.output.with_suffix(".json").read_text())
    assert saved["operation_id"] == "op-stop"
    assert saved["state"] == "incomplete"
    with wave.open(saved["partial_path"]) as wav:
        assert wav.getnframes() == 1
