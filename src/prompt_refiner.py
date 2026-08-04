from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib import error, request

DEFAULT_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"


def load_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _extract_text(data: dict[str, Any]) -> str:
    choices = data.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [
            part.get("text", "") for part in content if part.get("type") in {"text", "output_text"}
        ]
        return "\n".join(part for part in parts if part).strip()
    return ""


def refine_prompt(
    prompt: str, instructions: str = "", model: str = "nvidia/nemotron-3-super-120b-a12b"
) -> str:
    api_key = os.environ.get("NIM_API_KEY", "").strip() or os.environ.get("NGC_API_KEY", "").strip()
    if not api_key:
        return prompt

    base_url = os.environ.get("NIM_BASE_URL", "").strip() or DEFAULT_NIM_BASE_URL
    endpoint = base_url.rstrip("/") + "/chat/completions"

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You refine AI video prompts. Preserve the user's structure, scene continuity rules, "
                    "first-frame-only logic, and negative prompt. Improve clarity and continuity only."
                ),
            },
            {
                "role": "user",
                "content": f"Instructions:\n{instructions.strip()}\n\nPrompt:\n{prompt.strip()}",
            },
        ],
        "temperature": 0.2,
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
        with request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"HTTP {exc.code} {exc.reason}: {body or 'empty response body'}"
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(f"URL error: {exc.reason}") from exc

    return _extract_text(data) or prompt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refine a prompt with NVIDIA NIM if an API key is available."
    )
    parser.add_argument("prompt_file")
    parser.add_argument("--instructions", default="")
    parser.add_argument("--model", default="nvidia/nemotron-3-super-120b-a12b")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    refined = refine_prompt(load_text(args.prompt_file), args.instructions, args.model)
    if args.output == "-":
        print(refined)
    else:
        Path(args.output).write_text(refined, encoding="utf-8")


if __name__ == "__main__":
    main()
