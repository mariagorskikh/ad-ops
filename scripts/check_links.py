#!/usr/bin/env python3
"""Fetch ad landing URLs the way a browser would and report what the site would see.

  check_links.py <url> [<url> ...]   # the exact URLs a platform will send (copy them from the preview)
  check_links.py --ledger            # every live ad's landing URL from the ledger
  check_links.py --file urls.txt     # one URL per line

Flags a URL as BAD when:
  - the final status is not 200
  - a redirect dropped the query string (UTMs lost)
  - the path starts with /utm_ (a platform stripped the "?" and glued the query onto the path)
  - a required UTM parameter is missing (utm.required in the config)
  - the host is not the brand domain from the config (use --any-domain to skip)
  - utm_content does not match creative_id_pattern from the config

Platform macros like {{campaign.id}}, {campaignid} and {{CAMPAIGN_ID}} are replaced with
"test" before fetching, so the URL can be checked before the platform fills them in.
Stdlib only. Exit code 1 when any URL is BAD.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config  # noqa: E402

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
MACRO = re.compile(r"\{\{?[A-Za-z_.]+\}?\}")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def fetch(url: str, max_hops: int = 10):
    """Return (status, final_url, chain). Follows redirects by hand so each hop is visible."""
    chain = []
    cur = url
    for _ in range(max_hops):
        req = urllib.request.Request(cur, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        try:
            resp = OPENER.open(req, timeout=20)
            return resp.status, cur, chain
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
                nxt = urljoin(cur, e.headers["Location"])
                chain.append((e.code, nxt))
                cur = nxt
                continue
            return e.code, cur, chain
        except Exception as e:  # noqa: BLE001
            return 0, f"{type(e).__name__}: {e}", chain
    return 0, "too many redirects", chain


def judge(url: str, cfg: dict, any_domain: bool):
    test = MACRO.sub("test", url)
    code, final, chain = fetch(test)
    problems = []
    parts = urlsplit(url)
    if parts.path.startswith("/utm_") or "/utm_source=" in parts.path:
        problems.append("query stripped: the path holds utm_ params (a platform dropped the '?')")
    q = parse_qs(parts.query, keep_blank_values=True)
    for req in _config.get(cfg, "utm.required", []) or []:
        if req not in q or not q[req][0]:
            problems.append(f"missing {req}")
    pat = _config.get(cfg, "utm.creative_id_pattern")
    if pat and q.get("utm_content") and not MACRO.search(q["utm_content"][0]):
        if not re.match(pat, q["utm_content"][0]):
            problems.append(f"utm_content {q['utm_content'][0]!r} does not match {pat}")
    domain = _config.get(cfg, "brand.domain")
    if domain and not any_domain:
        host = (parts.hostname or "").lower()
        if host != domain and not host.endswith("." + domain):
            problems.append(f"host {host!r} is not {domain}")
    if code != 200:
        problems.append(f"HTTP {code}" if code else f"fetch failed: {final}")
    if chain and "utm_" in parts.query and "utm_" not in urlsplit(final).query:
        problems.append("redirect dropped the query (UTMs lost)")
    if "#" in url and "?" in url and url.index("#") < url.index("?"):
        problems.append("fragment before query: params after '#' never reach the server")
    return code, final, chain, problems


def ledger_urls() -> list[str]:
    import ledger  # local module
    rows = ledger.read_rows(ledger.ledger_path(None))
    out = []
    for r in ledger.latest(rows).values():
        if str(r.get("status", "")).startswith("live") and r.get("landing"):
            out.append(r["landing"])
    return sorted(set(out))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--ledger", action="store_true", help="check every live landing URL in the ledger")
    ap.add_argument("--file", help="file with one URL per line")
    ap.add_argument("--any-domain", action="store_true", help="do not require the brand domain")
    a = ap.parse_args()

    cfg = _config.load()
    urls = list(a.urls)
    if a.file:
        urls += [l.strip() for l in Path(a.file).read_text().splitlines() if l.strip() and not l.startswith("#")]
    if a.ledger:
        urls += ledger_urls()
    if not urls:
        ap.error("give URLs, --file or --ledger")

    bad = 0
    for u in urls:
        code, final, chain, problems = judge(u, cfg, a.any_domain)
        bad += bool(problems)
        print(f"{'ok ' if not problems else 'BAD'} {code} {u}")
        for c, hop in chain:
            print(f"      {c} -> {hop}")
        for p in problems:
            print(f"      ! {p}")
    print(f"\n{len(urls)} urls, {bad} with problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
