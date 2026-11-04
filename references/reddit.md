# Reddit Ads

Click paths as of 2026. Some agent setups cannot open reddit.com at all. Set `platforms.reddit.hands: user` in the config in that case: you write the brief, the user clicks, you verify from analytics. The same pattern works for any platform the agent cannot reach.

## When the user does the clicks

1. **Write the brief** in `<plans_dir>/<batch>-reddit.md`: campaign, objective, ad groups with targeting, every ad's title, body or headline, destination URL with `{{CAMPAIGN_ID}}`, `{{ADGROUP_ID}}`, `{{AD_ID}}` macros (build with `utm.py --platform reddit`), community and interest lists, click path, settings that must be off. One file the user can follow top to bottom.
2. **Collect the media** in one folder named by creative ID (1080x1080 squares and 4:5 work in feed; check current specs).
3. **Verify from analytics**, not by asking the user to read the UI back. Then log the ledger rows with the IDs they give you or that show up in `utm_campaign`.

## When the agent can click

- Campaigns, ad groups and ads tables at `https://ads.reddit.com`. Status toggles are in each row. Budget is on the campaign or ad group, depending on setup.
- Destination URL is per ad. Paste the full `utm.py` URL with macros; read it back before saving.

## Verifying a launch from analytics

Run `traffic_sql.py --since <launch day> --source reddit`, or in PostHog:

```sql
SELECT toStartOfHour(timestamp) AS hour, properties.utm_content AS content, properties.utm_campaign AS campaign,
       count() AS views, uniq(distinct_id) AS visitors, any(properties.$current_url) AS url
FROM events WHERE event = '$pageview' AND properties.utm_source = 'reddit'
  AND timestamp >= toDateTime('2026-03-01 00:00:00')
GROUP BY hour, content, campaign ORDER BY hour DESC LIMIT 50
```

- `campaign` is a long number and the URL carries `rdt_cid=`: a real ad click. The macros resolved and the destination is right.
- `campaign` is the literal `{{CAMPAIGN_ID}}`: someone clicked the preview inside the editor. Not an ad click, but it proves which creatives were built.
- If Reddit Ads data syncs into your warehouse, spend is often stored in micros (`sum(spend) / 1e6`). Check the latest synced date first.

## Rules of thumb

- One targeting type per ad group (communities or interests or keywords), so results are readable.
- Turn audience expansion off at first.
- Leave comments on and reply within hours; Reddit users judge the brand by the replies.
- Use a Traffic objective until the pixel has a meaningful number of conversion events, then try a conversion objective.
- Text ads written in a founder's plain voice often beat polished image ads on CTR.

## "What did I post?"

Run the query for the launch day. List creatives with real clicks, creatives seen only as previews, and what is missing or should be paused. Say whether the URLs matched the brief: macros resolved, `utm_content` present, 200 on the landing.
