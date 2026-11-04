---
name: ad-ops
description: Operate paid ad accounts after the creative exists. Set up campaigns, ad groups and ads on Google Ads, Meta (Facebook and Instagram), X and Reddit; review what is live; edit copy, keywords, URLs and budgets; pause, resume and delete; verify every link and UTM; read performance from your analytics (PostHog, GA4, Plausible) and the platform UIs; keep a change ledger and a launch plan. Use when the user says "set up the ads", "publish the ads", "pause this ad", "resume the campaign", "change the budget", "update the keywords", "fix the links", "fix the UTMs", "fix tracking", "are the ads running", "what is live", "ads status", "how are the ads doing", "which ad is winning", "edit the ad", "delete that ad", or anything that touches an ad account. Every account change needs the user's okay on the exact change; status reads and reports never do.
---

# ad-ops

Creative is made somewhere else (a designer, a creative skill, a folder of files). ad-ops runs the accounts: **set up, review, edit, measure, record.**

## Before anything

1. Load the config: `config.yaml` next to this file, or the path in `$AD_OPS_CONFIG`. If it is missing, copy `config.example.yaml`, ask the user for the brand domain, platforms in use and analytics tool, and fill it in. Never guess account IDs.
2. Read the ledger (`python3 scripts/ledger.py live`) so you know what should be running.
3. Read the platform file for the platform you will touch.

| what | where |
| --- | --- |
| Account IDs, analytics tool, budgets, approval rules | `config.yaml` |
| Click paths and UI traps per platform (as of 2026, UIs change) | `references/google.md`, `references/meta.md`, `references/x.md`, `references/reddit.md` |
| Driving ad UIs from a browser automation tool without mis-clicks | `references/browser.md` |
| Where each account lives, what to record about it | `references/accounts.md` |
| UTM scheme, proving tracking works, broken-link patterns, pixels and conversion events | `references/tracking.md` |
| Daily health check, weekly review, decision rules, report template | `references/review.md` |

## Hard rules

1. **One approval per change.** Reading, screenshotting, querying analytics and writing reports need no approval. Creating, editing, pausing, resuming, deleting, re-budgeting, changing bids or publishing anything in an ad account needs the user's okay on that exact change, in chat, in this session. Say what will change, where, from what to what, then wait. "Pause these three, swap the URL, then turn them back on" is one approval for that sequence on those ads. A new idea mid-task is a new approval.
2. **Money is the user's call.** Never raise a budget or bid above the caps in `budgets` without the user raising the cap in chat. Never accept platform "recommendations", never turn on auto-apply, never enable automatic budget increases. Never enter, change or confirm payment methods or billing details: hand that to the user.
3. **Never complete a re-auth.** "Confirm it's you", passwords, 2FA, security checks and CAPTCHAs belong to the user. Stop, ask them to do it, then redo the pending action, because it was almost always not saved.
4. **Right account only.** Work only in the accounts listed in the config. If a platform has both a personal and a business account (X does), confirm the account switcher shows the business account before every edit.
5. **Every URL is tracked and tested.** Build it with `scripts/utm.py`. Prove it with `scripts/check_links.py` on the exact URL the platform will send (status 200, query intact, on the brand domain). Within a day, confirm a real visit with that `utm_content` shows up in analytics (`references/tracking.md`).
6. **Verify after saving.** Reload and read the table back. Several UIs show optimistic state that was never committed.
7. **Record everything.** One ledger row per change (`scripts/ledger.py log ... approved="..."`), and update the current launch plan in `ledger.plans_dir`. A change that is not in the ledger did not happen.
8. **Copy follows the brand rules.** If `creative.copy_rules_file` is set, check every new headline, description, post text or keyword list against it before it goes live. Respect each platform's character limits. Do not invent claims (prices, guarantees, numbers) that are not in the approved copy.
9. **Judge on real outcomes.** Platform clicks and "conversions" are not comparable across platforms. Cost per conversion per `utm_content`, measured in your own analytics, is the number that decides.

## The jobs

### Status ("what is live", "are the ads running")
1. `python3 scripts/ledger.py live` for the expected state.
2. Platform truth: open each enabled platform's campaigns and ads tables (paths in the platform files). Note status, delivery, budget, disapprovals, "limited" states.
3. `python3 scripts/check_links.py --ledger` on every live landing URL.
4. `python3 scripts/traffic_sql.py --since <date>` and run the queries (or `--run` on PostHog) to see which creatives actually send visits and whether any old `utm_content` still gets traffic.
5. Report one table per platform: campaign, ad, status, budget, URL ok, last analytics hit. Flag every mismatch between ledger and platform. Fix the ledger with a `note` row; propose platform fixes as a numbered list.

### Set up (new campaign or new ads)
1. Collect the inputs: creative files, copy per platform, landing page, audience, budget. Ask for anything missing. Confirm the budget is within the caps.
2. Write the launch plan first (`<plans_dir>/<batch>.md`): campaigns, ad groups, every ad's text and file, URL, budget, settings that must be off. Show it to the user. Their okay on the plan is the approval for building exactly that plan.
3. Build URLs with `utm.py`, check them with `check_links.py` before you paste them anywhere.
4. Follow the platform file's click path. Upload the exact files from the plan. Read the copy back in the preview before publishing.
5. Publish. Then verify (rule 6), and write one ledger row per ad with the platform IDs.

### Edit (copy, keywords, URLs, budget, bids, pause, resume, delete)
1. State the exact change and get the okay (rule 1).
2. Prefer editing in place. Duplicating an ad often re-enables automatic enhancements; switch them off again.
3. For text fields: focus the real input first, select all, type, Tab, then read the value back before saving. Typing into an unfocused page does nothing, or worse, types into the wrong field.
4. After saving: reload, verify, run `check_links.py` if a URL changed, log the ledger row, update the launch plan.
5. Deleting is permanent on most platforms and loses history. Suggest pausing unless the user asked for delete.

### Review ("how are the ads doing", "which ad is winning")
Follow `references/review.md`: spend per platform, visits and conversions per `utm_content` from analytics, the decision rules from `review` in the config. Write the review to `ledger.reviews_dir`, show it in chat, propose changes as a numbered list, apply only the approved items.

### Tracking fixes ("fix the links", "fix the UTMs", "fix tracking")
Follow `references/tracking.md`: the common failure modes (stripped `?`, stale `utm_content` inside an ad, macro previews, missing Google suffix, fragment before query), how to confirm each one is gone, and how to check pixels and conversion events.

## Scripts

All stdlib Python 3.9+. PyYAML is used for the config if installed; otherwise a built-in parser reads it.

| script | use |
| --- | --- |
| `scripts/utm.py --platform meta --creative spring-hero-01` | build a tracked URL from the config's UTM scheme (`--suffix` for Google, `--fields` for tracking panels) |
| `scripts/check_links.py [URL ...] [--ledger] [--file f]` | fetch each URL with a browser user agent; report status, redirect chain, lost query, missing UTMs, wrong domain |
| `scripts/ledger.py init / log / live / show / history` | append-only change ledger, CSV or JSONL |
| `scripts/traffic_sql.py --since YYYY-MM-DD [--source x] [--run]` | analytics queries per creative: HogQL for PostHog (default), BigQuery SQL for GA4, Stats API URLs for Plausible |

## Pairing with a creative skill

ad-ops does not write ads. If you also use a skill or process that produces creative, point `creative.source_dir` at its output and `creative.copy_rules_file` at its rules. ad-ops reads those files and runs the accounts.
