# Google Ads

Click paths as of 2026. Google changes the UI often; if a step does not match, screenshot and adapt, then update this file.

## URLs

Keep the account query params Google adds (`ocid`, `__u`, `__c`, `authuser`) on every deep link. Paths: overview `/aw/overview`, campaigns `/aw/campaigns`, ad groups `/aw/adgroups?campaignId=...`, ads `/aw/ads?campaignId=...`, keywords `/aw/keywords?campaignId=...` (tabs Keywords and Negative keywords), RSA editor `/aw/ads/edit/search?campaignId=...&adId=...&adGroupIdForAd=...`.

## Click paths

- **Campaign status:** the status chip ("Enabled") at the top of a campaign page opens Enabled / Paused.
- **Budget:** click the "$X.00/day" chip, type, Save. "Eligible (Limited)" is normal for a small new campaign.
- **Ad group pause, enable, remove:** on `/aw/adgroups` hover the row, click the status dot in the row, pick Pause / Enable / Remove. Confirm the Status column after the table refreshes.
- **Edit a responsive search ad (RSA):** on `/aw/ads` hover the row, click the pencil at the right of the Ad cell. Close the "Ask Advisor" side pane first if it is open. Inputs in order: Final URL, Path 1, Path 2, up to 15 headlines (often no aria-label), then up to 4 descriptions (aria-label "Description"). Limits: headline 30, description 90, path 15 characters. "Save ad" at the bottom commits. Returning to `/aw/ads` means it saved.
- **Check an ad's final URL without opening it:** hover the row; the "Edit this Ad" button's aria-label often includes the final URL.
- **Clone an RSA for a landing-page test:** tick the ad > Edit > Copy > Edit > Paste > pick campaign and ad group > tick "Pause new ads after pasting" > Paste. Open the paused copy, change only the Final URL, Save, then Enable it. Two ads, one variable.
- **Add keywords:** `/aw/keywords` > "+" > select the ad group > textarea, one per line. Plain text is broad match, `"quotes"` phrase, `[brackets]` exact. New rows show "Under review". "Low search volume" is common for niche terms and is not an error.
- **Negative keywords:** same page, Negative keywords tab, "+", textarea. Keep a base list in the launch plan and add from search terms weekly.
- **Final URL suffix (where UTMs go):** account, campaign or ad group Settings > Additional settings > Campaign URL options > Final URL suffix. Paste `utm.py --platform google --suffix`. Put UTMs here, not in every final URL. Turn on auto-tagging too, so `gclid` arrives.

## Settings to check at launch (and keep off unless the user chose them)

- Search Partners and Display Network on a Search campaign.
- Broad match by default and AI-driven expansion features that rewrite your keywords or URLs.
- Auto-apply recommendations (Recommendations > Auto-apply). Never turn on; turn off if found and tell the user.
- Location option "Presence or interest" (prefer "Presence": people in the location).
- Automatically created assets, if the copy must stay exactly as approved.

## Conversions

Goals > Conversions > Summary. Check which actions are "Primary": those drive bidding. A page view marked as a primary conversion makes smart bidding chase page views. Prefer the real action (sign-up, purchase, lead form) via the Google tag, a GA4 import, or offline upload. See `tracking.md`.

## Reading performance

- In the UI: Campaigns, Ad groups, Ads, Keywords, and Insights and reports > Search terms. Default date range is often "Last 7 days" ending yesterday; set it explicitly.
- Columns worth adding: Impr., Clicks, CTR, Avg. CPC, Cost, Conversions, Cost / conv., Search impr. share.
- Warehouse sync (optional): if Google Ads data syncs into your analytics (PostHog data warehouse, BigQuery), cost is usually `metrics_cost_micros / 1e6`. Always check the latest synced date first; syncs stall silently.
- Ad strength "Poor" or "Incomplete" is advice, not a rule. It mostly wants more headlines.

## Traps

- "Confirm it's you" blocks every save until the user clicks it. The pending edit is lost; redo it.
- Select-all with nothing focused selects the page. Focus the input first.
- Every settings section has its own Save. "Done" in ad group creation saves nothing by itself.
- "Not eligible: Ad group paused" on an ad is the ad group's state, not a disapproval.
- A campaign in "Learning" after a big budget or bid change: do not judge it for several days.
