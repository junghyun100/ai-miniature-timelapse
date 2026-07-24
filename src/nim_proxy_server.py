from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict
from urllib import request


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"


def _extract_text(data: Dict[str, Any]) -> str:
    choices = data.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [part.get("text", "") for part in content if part.get("type") in {"text", "output_text"}]
        return "\n".join(part for part in parts if part).strip()
    return ""


def generate_with_nim(prompt_text: str, api_key: str, model: str, base_url: str) -> str:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You generate polished AI video prompt packs. Keep the same structure, preserve all rules, "
                    "and return English only."
                ),
            },
            {
                "role": "user",
                "content": prompt_text,
            },
        ],
        "temperature": 0.35,
    }
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return _extract_text(data) or prompt_text


class NIMHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/nim/generate":
            self._send_json(404, {"error": "not_found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length).decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json"})
            return

        api_key = (payload.get("api_key") or os.environ.get("NIM_API_KEY") or os.environ.get("NGC_API_KEY") or "").strip()
        model = (payload.get("model") or os.environ.get("NIM_MODEL") or "meta/llama-3.1-8b-instruct").strip()
        base_url = (payload.get("base_url") or os.environ.get("NIM_BASE_URL") or DEFAULT_NIM_BASE_URL).strip()
        prompt_text = (payload.get("prompt_text") or "").strip()
        if not api_key or not prompt_text:
            self._send_json(400, {"error": "missing_api_key_or_prompt"})
            return

        try:
            generated = generate_with_nim(prompt_text, api_key, model, base_url)
        except Exception as exc:  # pragma: no cover - surfaced to UI
            self._send_json(502, {"error": "nim_request_failed", "message": str(exc)})
            return

        self._send_json(200, {"text": generated, "model": model})


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local proxy for NVIDIA NIM prompt generation.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), NIMHandler)
    print(f"NIM proxy listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
