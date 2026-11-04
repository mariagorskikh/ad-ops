#!/usr/bin/env python3
"""Build a tracked landing URL from the UTM scheme in the config.

  utm.py --platform meta --creative spring-hero-01
  utm.py --platform google --suffix                  # account-level final URL suffix (no landing)
  utm.py --platform x --creative spring-hero-01 --campaign spring-launch --landing https://acme.com/pricing
  utm.py --platform x --creative spring-hero-01 --campaign spring-launch --fields   # values for X's tracking panel

utm_campaign and utm_term default to the platform macros in the config, so the platform
fills in its own ids. Fragments (#section) are kept at the very end, after the query.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config  # noqa: E402

SEARCH = {"google"}


def params(cfg: dict, platform: str, creative: str | None, campaign: str | None, term: str | None) -> dict:
    src = _config.get(cfg, f"utm.source_names.{platform}", platform)
    medium = _config.get(cfg, "utm.medium.search" if platform in SEARCH else "utm.medium.social",
                         "paid_search" if platform in SEARCH else "paid_social")
    camp = campaign or _config.get(cfg, f"utm.campaign_macros.{platform}", "")
    trm = term or _config.get(cfg, f"utm.term_macros.{platform}", "")
    p = {"utm_source": src, "utm_medium": medium}
    if camp:
        p["utm_campaign"] = camp
    if creative:
        p["utm_content"] = creative
    if trm:
        p["utm_term"] = trm
    return p


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platform", required=True)
    ap.add_argument("--creative", help="creative id, becomes utm_content")
    ap.add_argument("--campaign", help="override utm_campaign (required on platforms without a macro)")
    ap.add_argument("--term", help="override utm_term")
    ap.add_argument("--landing", help="landing URL (default brand.default_landing)")
    ap.add_argument("--suffix", action="store_true", help="print only the query string, for Google's final URL suffix")
    ap.add_argument("--fields", action="store_true", help="print one field per line, for tracking panels")
    a = ap.parse_args()

    cfg = _config.load()
    pat = _config.get(cfg, "utm.creative_id_pattern")
    if a.creative and pat and not re.match(pat, a.creative):
        sys.exit(f"creative id {a.creative!r} does not match {pat}")
    p = params(cfg, a.platform, a.creative, a.campaign, a.term)
    if "utm_campaign" not in p:
        sys.exit(f"{a.platform} has no campaign macro in the config: pass --campaign <slug>")
    for req in _config.get(cfg, "utm.required", []) or []:
        if req == "utm_content" and a.suffix:
            continue
        if req not in p:
            sys.exit(f"missing {req}: pass it on the command line")

    if a.fields:
        for k, v in p.items():
            print(f"{k}: {v}")
        return
    q = urlencode(p, safe="{}.")
    if a.suffix:
        print(q)
        return
    landing = a.landing or _config.get(cfg, "brand.default_landing")
    if not landing:
        sys.exit("no --landing and no brand.default_landing in the config")
    s = urlsplit(landing)
    existing = urlencode(parse_qsl(s.query), safe="{}.")
    query = f"{existing}&{q}" if existing else q
    print(urlunsplit((s.scheme, s.netloc, s.path or "/", query, s.fragment)))


if __name__ == "__main__":
    main()
