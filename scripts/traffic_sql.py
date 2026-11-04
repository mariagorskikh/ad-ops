#!/usr/bin/env python3
"""Print (or run) the analytics queries that show which ads really send visits and conversions.

  traffic_sql.py --since 2026-03-01                 # all paid traffic
  traffic_sql.py --since 2026-03-01 --source meta   # one utm_source
  traffic_sql.py --since 2026-03-01 --run           # PostHog only: run the queries over the API

The dialect comes from analytics.tool in the config:
  posthog   HogQL (default). Paste into PostHog SQL, a PostHog MCP execute-sql call, or use --run.
  ga4       BigQuery SQL against the GA4 export table (analytics.ga4.bigquery_table).
  plausible No SQL. Prints Stats API breakdown URLs to call with your API key.
  none      Nothing to query. Judge on platform numbers and say so in the report.

Queries:
  Q1 visits per source, campaign and utm_content, with first and last hit
  Q2 utm_content values with traffic that the ledger does not list as live (stale URLs, unrecorded ads)
  Q3 literal platform macros ({{CAMPAIGN_ID}} etc.): editor preview clicks, not real ad clicks
  Q4 per-creative funnel: visitors, engaged (2+ pageviews), converted (analytics.conversion_event)
  Q5 PostHog only, when ad tables are synced: how fresh the spend data is

--run needs env vars named in the config (default POSTHOG_PROJECT_ID, POSTHOG_PERSONAL_API_KEY).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config  # noqa: E402


def live_creatives() -> list[str]:
    try:
        import ledger
        rows = ledger.read_rows(ledger.ledger_path(None))
        return sorted({r.get("utm_content") or r.get("creative_id") for r in ledger.latest(rows).values()
                       if str(r.get("status", "")).startswith("live") and (r.get("utm_content") or r.get("creative_id"))})
    except Exception:  # noqa: BLE001
        return []


def sql_list(values: list[str]) -> str:
    safe = [v for v in values if re.fullmatch(r"[A-Za-z0-9_.:-]+", v)]
    return ", ".join(f"'{v}'" for v in safe) or "''"


def posthog(since: str, source: str | None, cfg: dict) -> list[tuple[str, str]]:
    pv = _config.get(cfg, "analytics.pageview_event", "$pageview")
    conv = _config.get(cfg, "analytics.conversion_event", "$identify")
    src = f"AND properties.utm_source = '{source}'" if source else "AND properties.utm_medium LIKE 'paid%'"
    win = f"timestamp >= toDateTime('{since} 00:00:00')"
    live = sql_list(live_creatives())
    qs = [
        ("Q1 visits per source, campaign, creative", f"""SELECT properties.utm_source AS src, properties.utm_campaign AS campaign,
       properties.utm_content AS creative, count() AS views, uniq(distinct_id) AS visitors,
       min(timestamp) AS first_hit, max(timestamp) AS last_hit, any(properties.$current_url) AS sample_url
FROM events WHERE event = '{pv}' AND {win} {src}
GROUP BY src, campaign, creative ORDER BY src, views DESC LIMIT 100"""),
        ("Q2 creatives with traffic that the ledger does not list as live", f"""SELECT properties.utm_source AS src, properties.utm_content AS creative, count() AS views, max(timestamp) AS last_hit
FROM events WHERE event = '{pv}' AND {win} {src}
  AND properties.utm_content IS NOT NULL AND properties.utm_content NOT IN ({live})
GROUP BY src, creative ORDER BY views DESC LIMIT 50"""),
        ("Q3 literal macros = editor preview clicks", f"""SELECT properties.utm_source AS src, properties.utm_content AS creative, count() AS views, any(properties.$current_url) AS url
FROM events WHERE event = '{pv}' AND {win} {src}
  AND (toString(properties.utm_campaign) LIKE '%{{%' OR toString(properties.$current_url) LIKE '%{{%')
GROUP BY src, creative ORDER BY views DESC LIMIT 50"""),
        ("Q4 per-creative funnel (first touch)", f"""WITH ft AS (
  SELECT person_id, argMin(toString(properties.utm_source), timestamp) AS src,
         argMin(toString(properties.utm_content), timestamp) AS creative
  FROM events WHERE event = '{pv}' AND {win} {src}
  GROUP BY person_id),
engaged AS (SELECT person_id FROM events WHERE event = '{pv}' AND {win} GROUP BY person_id HAVING count() >= 2),
conv AS (SELECT DISTINCT person_id FROM events WHERE event = '{conv}' AND {win})
SELECT src, creative, count() AS visitors,
       countIf(person_id IN (SELECT person_id FROM engaged)) AS engaged_2pv,
       countIf(person_id IN (SELECT person_id FROM conv)) AS converted
FROM ft GROUP BY src, creative ORDER BY visitors DESC LIMIT 50"""),
    ]
    g = _config.get(cfg, "analytics.posthog.google_ads_tables")
    if g and re.fullmatch(r"[A-Za-z0-9_]+", str(g)):
        qs.append(("Q5 Google Ads sync freshness and spend", f"""SELECT max(segments_date) AS last_synced_day,
       sumIf(metrics_cost_micros, segments_date >= toDate('{since}')) / 1e6 AS spend_since,
       sumIf(metrics_clicks, segments_date >= toDate('{since}')) AS clicks_since
FROM {g}.campaign_stats"""))
    return qs


def ga4(since: str, source: str | None, cfg: dict) -> list[tuple[str, str]]:
    table = _config.get(cfg, "analytics.ga4.bigquery_table", "project.analytics_000000.events_*")
    conv = _config.get(cfg, "analytics.conversion_event", "sign_up")
    day = since.replace("-", "")
    src = (f"AND collected_traffic_source.manual_source = '{source}'" if source
           else "AND collected_traffic_source.manual_medium LIKE 'paid%'")
    base = f"FROM `{table}` WHERE _TABLE_SUFFIX >= '{day}'"
    url = "(SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location')"
    live = sql_list(live_creatives())
    return [
        ("Q1 visits per source, campaign, creative", f"""SELECT collected_traffic_source.manual_source AS src,
       collected_traffic_source.manual_campaign_name AS campaign,
       collected_traffic_source.manual_content AS creative,
       COUNT(*) AS views, COUNT(DISTINCT user_pseudo_id) AS visitors,
       MIN(TIMESTAMP_MICROS(event_timestamp)) AS first_hit, MAX(TIMESTAMP_MICROS(event_timestamp)) AS last_hit,
       ANY_VALUE({url}) AS sample_url
{base} AND event_name = 'page_view' {src}
GROUP BY src, campaign, creative ORDER BY src, views DESC LIMIT 100"""),
        ("Q2 creatives with traffic that the ledger does not list as live", f"""SELECT collected_traffic_source.manual_source AS src, collected_traffic_source.manual_content AS creative, COUNT(*) AS views
{base} AND event_name = 'page_view' {src}
  AND collected_traffic_source.manual_content IS NOT NULL
  AND collected_traffic_source.manual_content NOT IN ({live})
GROUP BY src, creative ORDER BY views DESC LIMIT 50"""),
        ("Q3 literal macros = editor preview clicks", f"""SELECT collected_traffic_source.manual_source AS src, COUNT(*) AS views, ANY_VALUE({url}) AS url
{base} AND event_name = 'page_view' {src} AND {url} LIKE '%{{%'
GROUP BY src ORDER BY views DESC LIMIT 50"""),
        ("Q4 per-creative funnel (first touch)", f"""WITH ft AS (
  SELECT user_pseudo_id,
         ARRAY_AGG(collected_traffic_source.manual_source ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS src,
         ARRAY_AGG(collected_traffic_source.manual_content ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS creative
  {base} AND event_name = 'page_view' {src} GROUP BY user_pseudo_id),
engaged AS (SELECT user_pseudo_id {base} AND event_name = 'page_view' GROUP BY user_pseudo_id HAVING COUNT(*) >= 2),
conv AS (SELECT DISTINCT user_pseudo_id {base} AND event_name = '{conv}')
SELECT src, creative, COUNT(*) AS visitors,
       COUNTIF(user_pseudo_id IN (SELECT user_pseudo_id FROM engaged)) AS engaged_2pv,
       COUNTIF(user_pseudo_id IN (SELECT user_pseudo_id FROM conv)) AS converted
FROM ft GROUP BY src, creative ORDER BY visitors DESC LIMIT 50"""),
    ]


def plausible(since: str, source: str | None, cfg: dict) -> list[tuple[str, str]]:
    site = _config.get(cfg, "analytics.plausible.site_id", "acme.com")
    flt = f"&filters=visit:utm_source%3D%3D{source}" if source else "&filters=visit:utm_medium%3D~paid"
    import datetime as dt
    today = dt.date.today().isoformat()
    base = f"https://plausible.io/api/v1/stats/breakdown?site_id={site}&period=custom&date={since},{today}{flt}"
    return [
        ("Q1 visitors per utm_content", f"GET {base}&property=visit:utm_content&metrics=visitors,pageviews,bounce_rate"),
        ("Q1b visitors per utm_campaign", f"GET {base}&property=visit:utm_campaign&metrics=visitors"),
        ("Q4 conversions per utm_content (needs a goal set up in Plausible)",
         f"GET {base}&property=visit:utm_content&metrics=visitors,events (add ;event:goal%3D%3D<Goal> to filters)"),
        ("Auth", "Header: Authorization: Bearer $" + str(_config.get(cfg, "analytics.plausible.api_key_env", "PLAUSIBLE_API_KEY"))),
    ]


def run_posthog(query: str, cfg: dict) -> None:
    host = str(_config.get(cfg, "analytics.posthog.host", "https://us.posthog.com")).rstrip("/")
    pid = os.environ.get(str(_config.get(cfg, "analytics.posthog.project_id_env", "POSTHOG_PROJECT_ID")))
    key = os.environ.get(str(_config.get(cfg, "analytics.posthog.api_key_env", "POSTHOG_PERSONAL_API_KEY")))
    if not (pid and key):
        sys.exit("set the PostHog project id and personal API key env vars named in the config")
    body = json.dumps({"query": {"kind": "HogQLQuery", "query": query}}).encode()
    req = urllib.request.Request(f"{host}/api/projects/{pid}/query/", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    cols = data.get("columns") or []
    print("\t".join(map(str, cols)))
    for row in data.get("results") or []:
        print("\t".join("" if v is None else str(v) for v in row))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", required=True, help="YYYY-MM-DD")
    ap.add_argument("--source", help="one utm_source, e.g. google, meta, x, reddit")
    ap.add_argument("--run", action="store_true", help="PostHog only: run each query over the API")
    a = ap.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.since):
        ap.error("--since must be YYYY-MM-DD")
    if a.source and not re.fullmatch(r"[A-Za-z0-9_.-]+", a.source):
        ap.error("--source must be a plain utm_source value")

    cfg = _config.load()
    tool = str(_config.get(cfg, "analytics.tool", "posthog")).lower()
    builders = {"posthog": posthog, "ga4": ga4, "plausible": plausible}
    if tool not in builders:
        print("analytics.tool is 'none': no site analytics to query. Use platform numbers and flag that "
              "platform clicks overcount real visits.")
        return
    for title, q in builders[tool](a.since, a.source, cfg):
        print(f"\n-- {title}")
        if a.run and tool == "posthog":
            run_posthog(q, cfg)
        else:
            print(q)


if __name__ == "__main__":
    main()
