from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict
from urllib import error, request


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


def generate_prompt(prompt_brief: str, model: str = "meta/llama-3.1-8b-instruct") -> str:
    api_key = os.environ.get("NIM_API_KEY", "").strip() or os.environ.get("NGC_API_KEY", "").strip()
    if not api_key:
        return prompt_brief

    base_url = os.environ.get("NIM_BASE_URL", "").strip() or DEFAULT_NIM_BASE_URL
    endpoint = base_url.rstrip("/") + "/chat/completions"

    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert AI video prompt generator. Produce a polished prompt pack in English only. "
                    "Preserve all required rules: first scene only gets a true first-frame prompt, later scenes inherit "
                    "the previous final frame, giant human hands only, no miniature people, and a negative prompt at the end."
                ),
            },
            {
                "role": "user",
                "content": prompt_brief,
            },
        ],
        "temperature": 0.4,
    }

    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {exc.reason}: {body or 'empty response body'}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"URL error: {exc.reason}") from exc

    return _extract_text(data) or prompt_brief


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a prompt pack with NVIDIA NIM.")
    parser.add_argument("brief_file")
    parser.add_argument("--model", default="meta/llama-3.1-8b-instruct")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    text = Path(args.brief_file).read_text(encoding="utf-8")
    generated = generate_prompt(text, args.model)
    if args.output == "-":
        print(generated)
    else:
        Path(args.output).write_text(generated, encoding="utf-8")


if __name__ == "__main__":
    main()
