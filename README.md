# ad-ops

A Claude Code skill that runs your paid ad accounts once the creative exists.

It sets up campaigns, ad groups and ads on Google Ads, Meta (Facebook and Instagram), X and Reddit. It reviews what is live, edits copy, keywords, URLs and budgets, pauses, resumes and deletes. It checks every link and UTM, reads performance from your analytics and the platform UIs, and keeps a ledger of every change.

Every change to an ad account needs your okay on that exact change. Reading, checking and reporting never do.

## Requirements

- [Claude Code](https://claude.com/claude-code).
- Python 3.9 or newer. The scripts use only the standard library. PyYAML is used if installed, but is not required.
- A browser automation tool for Claude (for example a Chrome extension or browser MCP) where you are already logged in to your ad accounts. The skill never logs in for you and never types passwords.
- Optional: an analytics tool. PostHog is the documented default; GA4 (BigQuery export) and Plausible are supported. With none, the skill falls back to platform numbers and says so.

## Install

```bash
git clone https://github.com/mariagorskikh/ad-ops ~/.claude/skills/ad-ops
```

For one project only, clone into `<project>/.claude/skills/ad-ops` instead.

## Configure

```bash
cd ~/.claude/skills/ad-ops
cp config.example.yaml config.yaml
```

Fill in:

- `brand`: your name, domain and default landing page.
- `platforms`: set `enabled` for each platform you use and add the account IDs.
- `utm`: the source names, mediums and macros. The defaults work for most teams.
- `analytics`: `posthog`, `ga4`, `plausible` or `none`, plus the conversion event you judge ads on.
- `budgets`: daily caps per platform and in total. The skill will not go past them without you raising the cap in chat.
- `ledger`: where the change ledger, launch plans and reviews live (CSV or JSONL).

Secrets stay in environment variables, never in the config. For `traffic_sql.py --run` on PostHog:

```bash
export POSTHOG_PROJECT_ID=12345
export POSTHOG_PERSONAL_API_KEY=...   # a personal API key with query read access
```

Use `AD_OPS_CONFIG=/path/to/config.yaml` to keep the config somewhere else, for example in a project repo.

Create the ledger:

```bash
python3 ~/.claude/skills/ad-ops/scripts/ledger.py init
```

## Example prompts

- "Set up the ads for the Spring Launch batch on Google and Meta."
- "Are the ads running?"
- "What is live right now?"
- "Pause the spring-hero-02 ad on Meta."
- "Change the Google budget to $15 a day."
- "Add these keywords to the Pricing ad group."
- "Fix the UTMs on the X posts."
- "Which ad is winning this week?"
- "How are the ads doing? Write the weekly review."

## How it works

1. **Reads first.** It loads the config, the ledger and the platform notes, then looks at the live platform tables.
2. **Plans before it builds.** New campaigns start as a launch plan in Markdown. Your okay on the plan is the approval to build exactly that.
3. **Asks before every change.** It states what will change, where, from what to what, and waits for you. Budgets and bids never go past your caps. It never accepts platform recommendations, never turns on auto-apply, never touches billing, and stops for any re-auth or 2FA prompt.
4. **Checks every link.** URLs are built from your UTM scheme and fetched before they go live: status 200, query intact, right domain, no stripped `?`.
5. **Verifies after saving.** It reloads and reads the table back, because ad UIs often show changes that never saved.
6. **Records everything.** Each change is one row in an append-only ledger, with who approved it.
7. **Judges on real outcomes.** Reviews compare cost per conversion per creative from your own analytics, not platform clicks.

## What's in the box

```
ad-ops/
  SKILL.md                 the skill: rules, jobs, scripts
  config.example.yaml      copy to config.yaml and fill in
  references/
    accounts.md            where each platform lives, what to record
    browser.md             driving ad UIs from a browser tool without mis-clicks
    google.md              Google Ads click paths, settings, traps
    meta.md                Meta Ads Manager click paths, settings, traps
    x.md                   X Ads click paths and the stripped-link trap
    reddit.md              Reddit Ads, including the "user clicks, agent verifies" pattern
    tracking.md            UTM scheme, proof steps, failure modes, pixels and conversions
    review.md              daily health check, weekly review, decision rules, report template
  scripts/
    utm.py                 build tracked URLs from the config
    check_links.py         fetch landing URLs and flag broken or stripped tracking
    ledger.py              append-only change ledger (CSV or JSONL)
    traffic_sql.py         per-creative analytics queries (PostHog HogQL, GA4 BigQuery, Plausible)
    _config.py             config loader shared by the scripts
```

Platform click paths are accurate as of 2026. Ad UIs change often; when a step no longer matches, the skill adapts and you can update the reference file.

## Pairing with a creative skill

ad-ops does not write ads. If you have a skill or process that produces images, video and copy, set `creative.source_dir` to its output folder and `creative.copy_rules_file` to its brand rules. ad-ops reads those files and runs the accounts.

## License

MIT. See [LICENSE](LICENSE).
