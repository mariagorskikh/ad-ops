# X Ads

Click paths as of 2026. X changes Ads Manager often; if a step does not match, screenshot and adapt, then update this file.

## Account

Always use the full URL: `https://ads.x.com/manager/<ads account id>/campaigns`. Campaign editor: `.../campaigns/<campaign id>/edit` (steps: campaign, ad group, ads, review). `ads.x.com/` alone opens whatever account the browser is logged in as, which is often a personal one. Check the account switcher shows the business account before every edit. Never create, edit or boost anything under a personal account unless the user says so for that change.

## The link trap

Typing `https://acme.com/?utm_source=x&...` into a post's "Website URL" box has been saved as `acme.com/utm_source=x&...` (the `?` dropped), which is a 404. Correct setup:

- Website URL: the bare landing, for example `https://acme.com`.
- Open "Add URL tracking" and fill Source, Medium, Campaign name and Content from `utm.py --platform x --campaign <slug> --creative <id> --fields`.
- No `#fragment` on the landing. X appends tracking after it, and everything after `#` never reaches the server.
- Check the live card link with `check_links.py`. The right form is `https://acme.com/?utm_source=x&utm_medium=paid_social&utm_campaign=...&utm_content=...` and returns 200.

## Click paths

- **Posts in the editor:** campaign edit > Ads step; the left nav lists the posts. Clicking a post by its visible text via JS is more reliable than coordinates. The trash icon is the last button inside the active nav item; a dialog confirms.
- **Add post:** "Add post" > name (`<creative id> <format>`) > post text > Website URL (bare) > headline > "Add media" > file input under "Drag and drop or click to upload" > Confirm > "Add URL tracking".
- **Budget:** campaign step, Daily budget, then Review > "Save changes".
- **Pause, resume:** campaigns table row buttons labelled "Pause" / "Resume", or the status control in the editor.
- **Save:** every edit ends with "Save changes" on the Review step. Reload and read the table back.

## Settings to check

- Placements: turn off any you did not choose (search, profiles, AI assistant placements).
- Brand safety and adjacency controls.
- Auto bid vs target cost, and any automatic budget raises.

## Known failures

- **Blank page or "This view could not be loaded HTTP 403":** almost always the wrong logged-in account (a personal account that is not a user on the business ads account). The editor may say the account was not found. Check the switcher; if the business account is missing, ask the user to log in to it or add their user to the ads account. Clearing caches does not fix permissions.
- **Video uploads that never register:** images are reliable, videos less so. After two failed tries, hand it to the user.

## Reading performance

Platform UI: campaigns table (Impressions, Spend, Link clicks), per post under the Ads tab. X link clicks run well above real visits (accidental taps, bots, prefetch). Judge on analytics visits per `utm_content`. `twclid` marks X traffic even without UTMs. X spend usually does not sync to analytics tools; read it from the UI.
