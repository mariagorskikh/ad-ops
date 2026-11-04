"""Load the ad-ops config.

Order: $AD_OPS_CONFIG, then config.yaml next to SKILL.md, then config.example.yaml.
Uses PyYAML when installed. Otherwise a small built-in parser that handles the subset
used by config.example.yaml: nested maps, scalars, quoted strings and inline [a, b] lists.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]


def config_path() -> Path:
    env = os.environ.get("AD_OPS_CONFIG")
    if env:
        return Path(env).expanduser()
    for name in ("config.yaml", "config.example.yaml"):
        p = SKILL_DIR / name
        if p.exists():
            return p
    sys.exit("no config found: copy config.example.yaml to config.yaml")


def _strip_comment(line: str) -> str:
    out, quote = [], None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _scalar(v: str):
    v = v.strip()
    if v == "" or v in ("~", "null"):
        return None if v else ""
    if v[0] in "\"'" and v[-1] == v[0]:
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_scalar(x) for x in inner.split(",")] if inner else []
    low = v.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v


def _mini_yaml(text: str) -> dict:
    root: dict = {}
    stack = [(-1, root)]
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, val = line.strip().partition(":")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if val.strip() == "":
            child: dict = {}
            parent[key.strip()] = child
            stack.append((indent, child))
        else:
            parent[key.strip()] = _scalar(val)
    return root


def load() -> dict:
    p = config_path()
    text = p.read_text()
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except ImportError:
        return _mini_yaml(text)


def get(cfg: dict, dotted: str, default=None):
    cur = cfg
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur if cur is not None else default
