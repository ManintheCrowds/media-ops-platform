#!/usr/bin/env python3
"""
Standalone script to offload tasks to NVIDIA NIM (explain, refactor, add-tests, etc.).

Usage:
    python scripts/nim_batch.py "explain this code" path/to/file.py
    python scripts/nim_batch.py "add docstrings" path/to/module.py --model mistralai/codestral-22b-instruct-v0.1
    python scripts/nim_batch.py "summarize" path/to/log.txt --output summary.txt

Batch mode (--dir):
    python scripts/nim_batch.py "add docstrings" --dir job-automation-service/app/services/
    python scripts/nim_batch.py "summarize" --dir logs/ --glob "*.log" --output-dir summaries/

Args:
    prompt       Task prompt (e.g. "explain this code", "add docstrings")
    file_path    Path to file (omit when using --dir)
    --dir PATH   Process all matching files in directory
    --glob PATTERN  File pattern when using --dir (default: *.py)
    --output-dir PATH  Write each batch result to {output_dir}/{stem}.out
    --model      NIM model (default: meta/llama-3.1-8b-instruct)
    --output, -o Write response to file (single-file mode)

Requires: openai, python-dotenv (pip install openai python-dotenv)
Env: NVIDIA_API_KEY or (OPENAI_API_KEY + OPENAI_BASE_URL for NIM)
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

# Load .env from software root
_script_dir = Path(__file__).resolve().parent
_software_root = _script_dir.parent
_env_file = _software_root / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass

# Resolve API key and base URL
def _get_nim_config():
    import os
    api_key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL") or "https://integrate.api.nvidia.com/v1"
    return api_key, base_url


async def run_nim(prompt: str, file_path: Path, model: str, output_path: Optional[Path]) -> str:
    """Send prompt + file content to NIM and return response."""
    from openai import AsyncOpenAI

    api_key, base_url = _get_nim_config()
    if not api_key:
        raise SystemExit(
            "Error: Set NVIDIA_API_KEY or OPENAI_API_KEY in .env or environment."
        )

    content = file_path.read_text(encoding="utf-8", errors="replace")
    user_content = f"{prompt}\n\n---\n\n```\n{content}\n```"

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Respond concisely and accurately."},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
    )
    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise SystemExit("Error: Empty response from NIM.")

    if output_path:
        output_path.write_text(text, encoding="utf-8")
        print(f"Wrote {output_path}", file=sys.stderr)
    else:
        print(text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offload tasks to NVIDIA NIM (explain, refactor, add-tests, summarize)."
    )
    parser.add_argument("prompt", help="Task prompt (e.g. 'explain this code', 'add docstrings')")
    parser.add_argument(
        "file_path",
        type=Path,
        nargs="?",
        default=None,
        help="Path to file to process (omit when using --dir)",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        metavar="PATH",
        help="Process all matching files in directory (mutually exclusive with file_path)",
    )
    parser.add_argument(
        "--glob",
        default="*.py",
        help="File pattern when using --dir (default: *.py)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write each batch result to {output_dir}/{stem}.out",
    )
    parser.add_argument(
        "--model",
        default="meta/llama-3.1-8b-instruct",
        help="NIM model (default: meta/llama-3.1-8b-instruct)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Write response to file instead of stdout (single-file mode)",
    )
    args = parser.parse_args()

    if args.dir is not None and args.file_path is not None:
        raise SystemExit("Error: Use either file_path or --dir, not both.")
    if args.dir is None and args.file_path is None:
        raise SystemExit("Error: Provide file_path or --dir.")

    if args.dir is not None:
        if not args.dir.exists() or not args.dir.is_dir():
            raise SystemExit(f"Error: Directory not found: {args.dir}")
        files = sorted(args.dir.rglob(args.glob))
        files = [f for f in files if f.is_file()]
        if not files:
            raise SystemExit(f"Error: No files matching {args.glob} in {args.dir}")
        output_dir = args.output_dir
        if output_dir and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        async def run_batch():
            for fp in files:
                out = None
                if output_dir:
                    out = output_dir / f"{fp.stem}.out"
                try:
                    await run_nim(args.prompt, fp, args.model, out)
                except SystemExit as e:
                    print(f"Skipped {fp}: {e}", file=sys.stderr)

        asyncio.run(run_batch())
    else:
        if not args.file_path.exists():
            raise SystemExit(f"Error: File not found: {args.file_path}")
        asyncio.run(run_nim(args.prompt, args.file_path, args.model, args.output))


if __name__ == "__main__":
    main()
