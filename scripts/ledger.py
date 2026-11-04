#!/usr/bin/env python3
"""Append-only change ledger for ad accounts. CSV or JSONL, picked by file extension.

Every account change is one row. Rows are never edited; the current state of an ad
is its latest row. A change that is not in the ledger did not happen.

  ledger.py init
  ledger.py log platform=meta campaign="Spring Launch" ad="spring-hero-01 4x5" \
      creative_id=spring-hero-01 platform_id=1234567890 action=create status=live \
      budget_per_day=10 landing="https://acme.com/?utm_source=meta&utm_content=spring-hero-01" \
      approved="user in chat 2026-03-02" notes="first launch"
  ledger.py log platform=google creative_id=spring-rsa-01 action=pause status=paused \
      change="status live -> paused" approved="user in chat 2026-03-09"
  ledger.py live                      # latest row per ad where status is live
  ledger.py show spring-hero-01       # every row for a creative id, ad name, platform id or campaign
  ledger.py history --since 2026-03-01 [--platform meta]

Ledger path: --ledger, else $AD_OPS_LEDGER, else ledger.path in the config.
Actions: create, edit, copy, url, keywords, budget, bid, pause, resume, delete, tracking, note.
Every action except "note" needs approved=... (who approved and when).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config  # noqa: E402

COLUMNS = [
    "timestamp", "platform", "campaign", "ad_group", "ad", "creative_id", "platform_id",
    "action", "change", "status", "budget_per_day", "landing", "utm_content", "approved", "notes",
]
ACTIONS = {"create", "edit", "copy", "url", "keywords", "budget", "bid", "pause", "resume",
           "delete", "tracking", "note"}


def ledger_path(arg: str | None) -> Path:
    if arg:
        return Path(arg).expanduser()
    env = os.environ.get("AD_OPS_LEDGER")
    if env:
        return Path(env).expanduser()
    return Path(_config.get(_config.load(), "ledger.path", "ads/ledger.csv")).expanduser()


def is_jsonl(p: Path) -> bool:
    return p.suffix.lower() in (".jsonl", ".ndjson")


def read_rows(p: Path) -> list[dict]:
    if not p.exists():
        return []
    if is_jsonl(p):
        return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    with p.open(newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def append_row(p: Path, row: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    if is_jsonl(p):
        with p.open("a") as f:
            f.write(json.dumps({c: row.get(c, "") for c in COLUMNS}) + "\n")
        return
    new = not p.exists() or p.stat().st_size == 0
    with p.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow({c: row.get(c, "") for c in COLUMNS})


def key(r: dict) -> tuple:
    ident = r.get("platform_id") or r.get("creative_id") or r.get("ad") or r.get("campaign")
    return (r.get("platform", ""), ident)


def latest(rows: list[dict]) -> dict:
    state: dict = {}
    for r in rows:
        if r.get("action") == "note":
            continue
        k = key(r)
        merged = dict(state.get(k, {}))
        merged.update({c: v for c, v in r.items() if v not in ("", None)})
        state[k] = merged
    return state


def table(rows: list[dict], cols: list[str]) -> None:
    if not rows:
        print("(no rows)")
        return
    w = {c: max(len(c), *(len(str(r.get(c, ""))[:50]) for r in rows)) for c in cols}
    print("  ".join(c.ljust(w[c]) for c in cols))
    for r in rows:
        print("  ".join(str(r.get(c, ""))[:50].ljust(w[c]) for c in cols))


def parse_fields(fields: list[str]) -> dict:
    row = {}
    for f in fields:
        if "=" not in f:
            sys.exit(f"expected col=value, got {f!r}")
        k, v = f.split("=", 1)
        if k not in COLUMNS:
            sys.exit(f"unknown column {k!r}; columns: {', '.join(COLUMNS)}")
        row[k] = v
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", help="path to the ledger (.csv or .jsonl)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("log")
    p.add_argument("fields", nargs="+", help="col=value")
    sub.add_parser("live")
    p = sub.add_parser("show")
    p.add_argument("term")
    p = sub.add_parser("history")
    p.add_argument("--since", help="YYYY-MM-DD")
    p.add_argument("--platform")
    a = ap.parse_args()

    path = ledger_path(a.ledger)

    if a.cmd == "init":
        if path.exists() and path.stat().st_size:
            print(f"{path} already exists")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        if is_jsonl(path):
            path.write_text("")
        else:
            path.write_text(",".join(COLUMNS) + "\n")
        print(f"created {path}")
        return

    if a.cmd == "log":
        row = parse_fields(a.fields)
        for req in ("platform", "action"):
            if not row.get(req):
                sys.exit(f"log needs {req}=")
        if row["action"] not in ACTIONS:
            sys.exit(f"unknown action {row['action']!r}; use one of {', '.join(sorted(ACTIONS))}")
        if row["action"] != "note" and not row.get("approved"):
            sys.exit("account changes need approved=\"who and when\" (the user's okay on this exact change)")
        if not (row.get("creative_id") or row.get("platform_id") or row.get("ad") or row.get("campaign")):
            sys.exit("log needs at least one of creative_id, platform_id, ad, campaign")
        row["timestamp"] = row.get("timestamp") or dt.datetime.now().isoformat(timespec="seconds")
        if row.get("creative_id") and not row.get("utm_content"):
            row["utm_content"] = row["creative_id"]
        append_row(path, row)
        table([row], ["timestamp", "platform", "creative_id", "action", "status", "budget_per_day", "approved"])
        print(f"appended to {path}")
        return

    rows = read_rows(path)

    if a.cmd == "live":
        live = [r for r in latest(rows).values() if str(r.get("status", "")).startswith("live")]
        for plat in sorted({r.get("platform", "") for r in live}):
            print(f"\n== {plat} ==")
            table([r for r in live if r.get("platform") == plat],
                  ["campaign", "ad", "creative_id", "platform_id", "budget_per_day", "utm_content", "landing"])
        print(f"\n{len(live)} live ads")
        return

    if a.cmd == "show":
        t = a.term
        hits = [r for r in rows if t in (r.get("creative_id"), r.get("platform_id"), r.get("ad"), r.get("campaign"))]
        table(hits, ["timestamp", "platform", "ad", "action", "change", "status", "budget_per_day", "approved", "notes"])
        return

    if a.cmd == "history":
        hits = [r for r in rows
                if (not a.since or str(r.get("timestamp", "")) >= a.since)
                and (not a.platform or r.get("platform") == a.platform)]
        table(hits, ["timestamp", "platform", "campaign", "ad", "action", "change", "status", "approved"])
        print(f"\n{len(hits)} rows")


if __name__ == "__main__":
    main()
