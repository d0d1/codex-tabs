from __future__ import annotations

import os
from typing import Callable, TextIO


ANSI_RESET = "\033[0m"
ANSI_STYLES = {
    "header": "\033[1m",
    "accent": "\033[96m",
    "label": "\033[2m",
    "success": "\033[92m",
    "warning": "\033[93m",
    "error": "\033[91m",
    "prompt": "\033[1m",
}


def stream_supports_ansi(stream: TextIO) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(stream, "isatty") or not stream.isatty():
        return False
    return os.environ.get("TERM", "") != "dumb"


def styled(text: str, style_name: str, *, stream: TextIO) -> str:
    if not stream_supports_ansi(stream):
        return text
    code = ANSI_STYLES.get(style_name, "")
    if not code:
        return text
    return f"{code}{text}{ANSI_RESET}"


def label_text(text: str, *, stream: TextIO) -> str:
    return styled(text, "label", stream=stream)


def header_text(text: str, *, stream: TextIO) -> str:
    return styled(text, "header", stream=stream)


def accent_text(text: str, *, stream: TextIO) -> str:
    return styled(text, "accent", stream=stream)


def success_text(text: str, *, stream: TextIO) -> str:
    return styled(text, "success", stream=stream)


def warning_text(text: str, *, stream: TextIO) -> str:
    return styled(text, "warning", stream=stream)


def error_text(text: str, *, stream: TextIO) -> str:
    return styled(text, "error", stream=stream)


def prompt_text(text: str, *, stream: TextIO) -> str:
    return styled(text, "prompt", stream=stream)


def menu_line(key: str, text: str, *, output: TextIO) -> None:
    print(f"{accent_text(f'[{key}]', stream=output)} {text}", file=output)


def prompt_input(input_fn: Callable[[str], str], prompt: str, *, output: TextIO) -> str:
    return input_fn(prompt_text(prompt, stream=output))
