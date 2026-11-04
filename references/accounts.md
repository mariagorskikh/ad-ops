# Accounts

The IDs live in `config.yaml`. This file says where each account is, what to check, and what to record.

Verify every ID in the platform UI before you quote it to the user. When something changes (new campaign, new account, new pixel), update the config and log a `note` row in the ledger.

## Access

- Drive the platforms in a browser where the user is already logged in. Never log in for them, never type passwords, never complete a re-auth prompt.
- If an account will not load, check which user is logged in before anything else. Most "403" and "account not found" errors are the wrong login, not a bug.
- If the agent cannot open a site at all (some tools block certain domains), the user does the clicks from a brief you write. See `reddit.md` for that pattern; it works for any platform.

## Where each platform lives (as of 2026, UIs change)

| platform | home | ID you need | notes |
| --- | --- | --- | --- |
| Google Ads | `https://ads.google.com/aw/overview` | customer ID, shape 123-456-7890 | Keep the query params Google adds to the URL (`ocid`, `__u`, `__c`, `authuser`) when you build deep links, or you land in the wrong account. |
| Meta | `https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=<ad account id>` | ad account ID (the number after `act=`), Page, pixel or dataset ID | One Business portfolio can hold several ad accounts. Check the account picker. |
| X | `https://ads.x.com/manager/<ads account id>/campaigns` | ads account ID, business handle | `ads.x.com/` with no account path opens whatever account the browser is logged in as. Always use the full URL. |
| Reddit | `https://ads.reddit.com` | ads account ID, pixel ID | Campaign IDs show up as numbers in `utm_campaign` when you use the macro. |
| LinkedIn | `https://www.linkedin.com/campaignmanager/` | ad account ID, company page | Thought Leader ads boost a person's post and often beat company-page ads for small brands. |

## What to keep per account in the launch plan

- Campaign name and ID, objective, daily budget, bid strategy.
- Ad groups or ad sets with IDs and targeting in one line.
- Every ad: name, platform ID, creative ID (`utm_content`), file used, landing URL, status.
- Settings that must stay off (see each platform file).
- Where spend is read from (platform UI, or an analytics warehouse sync).

Keep names consistent: `<creative id> <format>` for ads (for example `spring-hero-01 4x5`) makes the ads table, the ledger and analytics line up. Ad names are cosmetic; `utm_content` is the key.
