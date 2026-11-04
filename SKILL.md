---
name: ad-ops
description: Operate paid ad accounts after the creative exists. Set up campaigns, ad groups and ads on Google Ads, Meta (Facebook and Instagram), X and Reddit; review what is live; edit copy, keywords, URLs and budgets; pause, resume and delete; verify every link and UTM; read performance from your analytics (PostHog, GA4, Plausible) and the platform UIs; keep a change ledger and a launch plan. Use when the user says "set up the ads", "publish the ads", "pause this ad", "resume the campaign", "change the budget", "update the keywords", "fix the links", "fix the UTMs", "fix tracking", "are the ads running", "what is live", "ads status", "how are the ads doing", "which ad is winning", "edit the ad", "delete that ad", or anything that touches an ad account. Runs on its own by default and reports after; only spending money (new paid campaigns, budget or bid increases, new accounts, anything over the caps) waits for the user's yes.
---

# ad-ops

Creative is made somewhere else (a designer, a creative skill, a folder of files). ad-ops runs the accounts: **set up, review, edit, measure, record.**

**Money is the only approval.** In the default `autonomous` mode the agent checks its own work and then makes account changes itself. It stops for the user's explicit yes in chat only when a change spends money or raises spend: launching a new campaign or ad set with a budget, raising any budget or bid, adding a new platform or account, or anything over the caps in `budgets`. Pausing and lowering spend are not spending; do them without asking.

## Before anything

1. **Ask once, up front.** Load the config: `config.yaml` next to this file, or the path in `$AD_OPS_CONFIG`. If it is missing, or a value the job needs is blank, copy `config.example.yaml` and ask the setup questions in one short batch: brand domain and default landing page, platforms in use and their account IDs, analytics tool and conversion event, daily budget caps, ledger location. Write the answers to the config, then continue without further questions. Never guess account IDs.
2. Later runs ask nothing. If a required fact is genuinely missing and cannot be found in the config, ledger, platform UI or analytics, ask one short question and keep working on everything else meanwhile.
3. Read the ledger (`python3 scripts/ledger.py live`) so you know what should be running.
4. Read the platform file for the platform you will touch.

| what | where |
| --- | --- |
| Account IDs, analytics tool, budgets, autonomy mode | `config.yaml` |
| Click paths and UI traps per platform (as of 2026, UIs change) | `references/google.md`, `references/meta.md`, `references/x.md`, `references/reddit.md` |
| Driving ad UIs from a browser automation tool without mis-clicks | `references/browser.md` |
| Where each account lives, what to record about it | `references/accounts.md` |
| UTM scheme, proving tracking works, broken-link patterns, pixels and conversion events | `references/tracking.md` |
| Daily health check, weekly review, decision rules, report template | `references/review.md` |

## What runs on its own, what waits for a yes

| autonomous (after the self-review gate) | needs the user's yes in chat (money) |
| --- | --- |
| Status checks, reviews, reports, analytics queries | Launching a new campaign or ad set with a budget |
| Copy, headline, description, keyword and negative keyword edits | Raising any budget or bid, by any amount |
| URL, UTM and tracking fixes | Adding a new platform or ad account |
| Pausing ads, ad groups or campaigns | Anything above the caps in `budgets` |
| Lowering budgets or bids | |
| Resuming an ad that was already running, within its existing budget | |
| Swapping a creative inside an existing ad group, budget unchanged | |
| Deleting, only when the user asked for delete | |

Once the user approves a launch plan or a spend change, build all of it without further questions.

## Hard stops

These are not approvals. They are stops. On any of them, halt that action, finish whatever else is safe, and report.

1. **Re-auth.** "Confirm it's you", passwords, 2FA, security checks and CAPTCHAs belong to the user. Ask them to do it, then redo the pending action, because it was almost always not saved.
2. **Billing.** Never enter, change or confirm payment methods or billing details.
3. **Platform warnings.** Policy warnings, disapprovals with an appeal path, account restrictions or limit notices. Do not appeal, click through or work around them; report them.
4. **Wrong account.** Work only in the accounts in the config. If a platform has both a personal and a business account (X does), confirm the switcher shows the business account before every edit. If it does not, stop.
5. **No invented facts.** Never write claims (prices, guarantees, numbers) that are not in the approved copy or brand rules.

## Rules for every change

1. **Self-review gate.** Before any account change: build the URL with `scripts/utm.py` and prove it with `scripts/check_links.py` (status 200, query intact, on the brand domain); check copy against `creative.copy_rules_file` if set and against each platform's character limits; re-read the change as the person seeing the ad would; confirm it stays inside the caps and the autonomy table above. Fix anything that fails, then act.
2. **Never accept platform "recommendations",** never turn on auto-apply, never enable automatic budget increases. Turn them off if found and say so.
3. **Verify after saving.** Reload and read the table back. Several UIs show optimistic state that was never committed. Within a day, confirm a real visit with that `utm_content` shows up in analytics (`references/tracking.md`).
4. **Record everything.** One ledger row per change (`scripts/ledger.py log ... approved="..."`). `approved` holds the authority for the change: `self-review, autonomous mode`, `user in chat <date>` for money or review mode, or `launch plan <batch> approved <date>`. Update the current launch plan in `ledger.plans_dir`. A change that is not in the ledger did not happen.
5. **Judge on real outcomes.** Platform clicks and "conversions" are not comparable across platforms. Cost per conversion per `utm_content`, measured in your own analytics, decides.
6. **Report after.** End every run with one summary: each change made (platform, ad, from what to what), the exact copy and URLs that went live, ledger rows written, anything skipped or stopped and why, and any money item waiting for a yes.

## The jobs

### Status ("what is live", "are the ads running")
1. `python3 scripts/ledger.py live` for the expected state.
2. Platform truth: open each enabled platform's campaigns and ads tables (paths in the platform files). Note status, delivery, budget, disapprovals, "limited" states.
3. `python3 scripts/check_links.py --ledger` on every live landing URL.
4. `python3 scripts/traffic_sql.py --since <date>` and run the queries (or `--run` on PostHog) to see which creatives actually send visits and whether any old `utm_content` still gets traffic.
5. Report one table per platform: campaign, ad, status, budget, URL ok, last analytics hit. Fix ledger drift with a `note` row. Fix broken URLs and tracking yourself (autonomous); list any money item for the user.

### Set up (new campaign or new ads)
1. Collect the inputs: creative files, copy per platform, landing page, audience, budget. Ask in one batch for anything missing. Confirm the budget is within the caps.
2. Write the launch plan (`<plans_dir>/<batch>.md`): campaigns, ad groups, every ad's text and file, URL, daily and total budget, settings that must be off. A new campaign or ad set with a budget is a money item: show the plan and its spend and wait for the user's yes. That yes covers building exactly that plan.
3. Run the self-review gate on every URL and line in the plan before pasting anything.
4. Follow the platform file's click path. Upload the exact files from the plan. Read the copy back in the preview before publishing.
5. Publish. Verify (rule 3), write one ledger row per ad with the platform IDs, and report.

New ads inside an existing ad group, with no budget change, skip step 2's wait.

### Edit (copy, keywords, URLs, budget, bids, pause, resume, delete)
1. Check the autonomy table. Budget or bid going up: state the change (where, from what to what, new daily spend) and wait for the yes. Everything else: run the self-review gate and proceed.
2. Prefer editing in place. Duplicating an ad often re-enables automatic enhancements; switch them off again.
3. For text fields: focus the real input first, select all, type, Tab, then read the value back before saving. Typing into an unfocused page does nothing, or worse, types into the wrong field.
4. After saving: reload, verify, run `check_links.py` if a URL changed, log the ledger row, update the launch plan.
5. Deleting is permanent on most platforms and loses history. Pause instead unless the user asked for delete.

### Review ("how are the ads doing", "which ad is winning")
Follow `references/review.md`: spend per platform, visits and conversions per `utm_content` from analytics, the decision rules from `review` in the config. Write the review to `ledger.reviews_dir` and show it in chat. Apply the non-money actions it calls for yourself (pause kill candidates, add negatives, fix links, rotate fatigued creative within budget). List scale candidates (budget increases) for the user's yes.

### Tracking fixes ("fix the links", "fix the UTMs", "fix tracking")
Follow `references/tracking.md`: the common failure modes (stripped `?`, stale `utm_content` inside an ad, macro previews, missing Google suffix, fragment before query), how to confirm each one is gone, and how to check pixels and conversion events. Fix them, verify, log, report.

## Review mode

Set `autonomy.mode: review` for the old per-change gates. Money rules and hard stops are the same. In addition:

- **One approval per change.** Reading, screenshotting, querying analytics and writing reports need no approval. Creating, editing, pausing, resuming, deleting, re-budgeting, changing bids or publishing anything in an ad account needs the user's okay on that exact change, in chat, in this session. Say what will change, where, from what to what, then wait. "Pause these three, swap the URL, then turn them back on" is one approval for that sequence on those ads. A new idea mid-task is a new approval.
- **Set up:** the user's okay on the launch plan is the approval for building exactly that plan.
- **Review:** propose changes as a numbered list and apply only the approved items.
- **Ledger:** `approved="user in chat <date>"` on every row.

## Scripts

All stdlib Python 3.9+. PyYAML is used for the config if installed; otherwise a built-in parser reads it.

| script | use |
| --- | --- |
| `scripts/utm.py --platform meta --creative spring-hero-01` | build a tracked URL from the config's UTM scheme (`--suffix` for Google, `--fields` for tracking panels) |
| `scripts/check_links.py [URL ...] [--ledger] [--file f]` | fetch each URL with a browser user agent; report status, redirect chain, lost query, missing UTMs, wrong domain |
| `scripts/ledger.py init / log / live / show / history` | append-only change ledger, CSV or JSONL; `log` refuses account changes without `approved=` |
| `scripts/traffic_sql.py --since YYYY-MM-DD [--source x] [--run]` | analytics queries per creative: HogQL for PostHog (default), BigQuery SQL for GA4, Stats API URLs for Plausible |

## Pairing with a creative skill

ad-ops does not write ads. If you also use a skill or process that produces creative, point `creative.source_dir` at its output and `creative.copy_rules_file` at its rules. ad-ops reads those files and runs the accounts.
