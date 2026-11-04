# Review: the daily health check and the weekly review

Reads and reports need no approval. In autonomous mode, the non-money changes a review calls for (pauses, negatives, link fixes, creative rotation within budget) are applied after the self-review gate. Budget increases wait for the user's yes. In review mode, every change waits for approval, item by item.

## Daily health check (a few minutes)

1. `ledger.py live` for the expected state.
2. Platform tables: is every expected ad active or eligible? Anything disapproved, "not eligible", "learning limited", "in review" for more than a day, or paused that should run? Do budgets match the ledger and stay under the caps?
3. `check_links.py --ledger` on live landing URLs.
4. `traffic_sql.py --since <yesterday>`: every live creative on a social platform should show at least one visit per day. Zero for two days on a live ad means the platform is not delivering or the link broke.
5. Report one table per platform (campaign, ad, status, budget, URL ok, last hit). Log a `note` row for any ledger drift. Propose platform fixes as a numbered list.

## Weekly review ("how are the ads doing", "which ad is winning")

1. **Spend per platform.** From the platform UI, or from a warehouse sync if you have one (check the latest synced date first; syncs stall silently).
2. **Visits and conversions per creative** from `traffic_sql.py` Q1 and Q4 for the week.
3. **Join to the ledger** so each row has platform, campaign, creative, budget and age.
4. **Apply the decision rules** from `review` in the config:
   - Do not judge before `min_impressions_before_judging` impressions and `min_days_before_judging` days.
   - Kill candidates: CTR below `kill_ctr_below_fraction_of_median` of the campaign median, or spend above `kill_cost_multiple_of_target` times the target cost per conversion with zero conversions.
   - Scale candidates: cost per conversion under target with enough volume. Raise by at most `budgets.scale_step_percent`, no more often than every `budgets.scale_min_days_between` days, never past the caps.
   - Fatigue: frequency above `fatigue_frequency`, or CTR down `fatigue_ctr_drop_percent` from its first week. Rotate the creative.
5. **Write it up** in `<reviews_dir>/<YYYY-MM-DD>.md` with the template below, and show it in chat.
6. **Act:** apply the non-money items (autonomous mode) or the approved items (review mode), then ledger, launch plan. List budget increases for the user's yes.

## What to look at per platform

- **Google:** impressions, clicks, CTR, avg CPC, cost per conversion, search terms (find junk intent and add negatives), keyword status, impression share lost to budget vs rank.
- **Meta:** per-ad CTR (link), CPC, frequency, cost per result; analytics visits and engaged visits per `utm_content`.
- **X:** impressions and link clicks per post; analytics visits per `utm_content` as the real count.
- **Reddit:** spend and clicks; analytics visits with `rdt_cid`; comments on the ad (the user replies).
- **Across all:** cost per conversion per creative, from your own analytics, is the only comparable number. Platform "results" and "conversions" use different definitions and attribution windows.

## Report template

```markdown
# Ads review YYYY-MM-DD (week of ...)

## Summary
Spend $X across N platforms. Y conversions. Best creative: <id> at $Z per conversion. One sentence on what changed since last week.

## Per platform
| platform | campaign | ad (creative id) | status | budget/day | spend | impr. | clicks | visits | conv. | cost/conv |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Issues found
- Broken links, disapprovals, stale utm_content, sync gaps.

## Changes made
1. Paused <ad> on <platform>: CTR 0.4% vs median 1.1% after 3,200 impressions.
2. Added negatives to <campaign>: "free", "jobs", "login".

## Waiting for your yes (money)
1. Raise <campaign> from $10 to $12/day: $18 per conversion vs $50 target, 9 conversions.
```

For each ad in the chat version, show its visual (file path), text, keywords where relevant, budget and numbers, so the user can decide without opening the platforms.
