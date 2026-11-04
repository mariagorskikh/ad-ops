# Tracking: scheme, proof, failure modes

## UTM scheme

Set in `config.yaml` under `utm`; `scripts/utm.py` builds URLs from it.

| param | value | notes |
| --- | --- | --- |
| `utm_source` | platform: google, meta, x, reddit, linkedin | lowercase, fixed per platform |
| `utm_medium` | `paid_search` or `paid_social` | keep the `paid` prefix so one filter finds all paid traffic |
| `utm_campaign` | platform campaign ID via macro, or a fixed slug | Google `{campaignid}`, Meta `{{campaign.id}}`, Reddit `{{CAMPAIGN_ID}}`; X needs a slug like `spring-launch` |
| `utm_content` | **your creative ID**, e.g. `spring-hero-01` | the review key; one value per creative; change it when the creative changes |
| `utm_term` | ad group ID or keyword via macro | optional |

Click IDs that arrive even without UTMs: `gclid` (Google), `fbclid` (Meta), `twclid` (X), `rdt_cid` (Reddit), `li_fat_id` (LinkedIn). Do not strip them on the site.

Google: put UTMs in the account or campaign Final URL suffix (`utm.py --platform google --suffix`), not in each final URL, and keep auto-tagging on.

## Proof, in order

1. **The URL itself.** `python3 scripts/check_links.py "<url>"` returns 200 on your domain with the query intact.
2. **The platform preview.** Read the rendered link (X card, Meta Preview URL, Google final URL plus suffix) and compare `utm_content` with the ledger.
3. **Analytics within a day.** `python3 scripts/traffic_sql.py --since <date>` prints the queries: visits per source and creative, stale `utm_content` values, macro preview clicks, and the per-creative funnel.
4. **Conversions.** The funnel query counts `analytics.conversion_event` per first-touch creative. On PostHog, filter with `IN (subquery)` rather than a LEFT JOIN on person_id; joins on person tables are slow and easy to get wrong.

## Failure modes

| symptom | cause | fix |
| --- | --- | --- |
| Visits with the right source exist, but the ad's link 404s; the URL path looks like `/utm_source=...` with no `?` | the platform stripped `?` from the URL box (seen on X) | bare landing in the URL box, UTMs in the platform's tracking panel |
| Analytics still reports an old `utm_content` after the creative changed | the ad's Website URL kept the old value; only the name or media changed | edit the destination URL in the ad, publish, check again next day |
| `utm_campaign={{CAMPAIGN_ID}}` or another literal macro | preview clicks inside the ad editor | ignore in reports; real clicks have numeric IDs and a click ID |
| Google `gclid` present but no `utm_*` | Final URL suffix missing | set the suffix; do not add UTMs to each final URL |
| UTMs present in the ad but missing on arrival | a redirect (http to https, apex to www, trailing slash) dropped the query | `check_links.py` shows the redirect chain; fix the redirect to keep the query, or point the ad at the final URL |
| Params after `#` never reach analytics | fragment placed before the query | query first, fragment last; or drop the fragment |
| Platform clicks far above analytics visits | accidental taps, bots, prefetch, consent banners blocking analytics | judge on analytics visits; narrow placements; check consent mode |

## Pixels and conversion events

- **Pick one conversion that matters** (sign-up, purchase, qualified lead) and set it as `analytics.conversion_event`. Page views are not conversions.
- **Platform pixels:** Google tag, Meta pixel (dataset), X pixel, Reddit pixel, LinkedIn Insight Tag. Each should fire on every page, plus a conversion event on the success page or after the success action.
- **Check they fire:** each platform has a live test view (Google Tag Assistant, Meta Events Manager > Test events, Reddit and X event managers). Load the landing page with the test tool open and do the conversion once.
- **Server-side events** (Meta Conversions API, Google enhanced conversions, Reddit CAPI) improve match rates as browsers block more. They are a developer task; write the request for the user's developer instead of changing code you do not own.
- **What the platform optimizes for** is the event marked primary (Google) or chosen in the ad set (Meta). If that event is a page view, smart bidding buys page views.
- **Consent:** if the site has a consent banner, pixels and analytics may not fire until accepted. Expect a gap between platform clicks and analytics visits.

## Site side

If a platform keeps stripping `?`, a small redirect on the site from `/utm_source=...` to `/?utm_source=...` rescues those links. Offer it to the user as a developer task; do not change site code yourself unless asked.
