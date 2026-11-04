# Meta (Facebook and Instagram)

Click paths as of 2026. Meta changes Ads Manager often; if a step does not match, screenshot and adapt, then update this file.

## URLs

- Ads table: `https://adsmanager.facebook.com/adsmanager/manage/ads?act=<ad account id>&selected_campaign_ids=<campaign id>`
- Standalone ad editor (fastest way to one ad): `https://adsmanager.facebook.com/adsmanager/manage/ads/edit/standalone?act=<ad account id>&selected_campaign_ids=<campaign id>&selected_ad_ids=<ad id>`
- Wait 10 to 15 seconds and scroll the left column once; sections render lazily.

## Editor map (left column, top to bottom)

Ad name; Partnership ad; Identity (Facebook Page, Instagram profile); Ad setup; Ad creative (Media card with a "+" tile and Upload; primary text is a contenteditable DIV, headline and description are inputs); creative extensions such as site summaries or highlights; Advantage+ creative enhancements (music, text variations, image edits; several hide under sub-tabs of that card); Call to action; Languages; **Destination** (Website URL, Display link; this card has been hidden with `display:none` in the standalone editor); Tracking (Website events, URL parameters); Publish bar.

## Click paths

- **Campaign or ad on/off:** the toggle in the table row. Check that Delivery changes.
- **Budget:** open the campaign (Advantage campaign budget) or ad set (ad set budget), click the Budget field, select all, type, Tab, Publish.
- **Website URL (tracking) fix:** open the ad in the standalone editor, un-hide Destination if needed (see `browser.md`), focus the Website URL input by reference, select all, paste the `utm.py --platform meta` URL (keeps `{{campaign.id}}`, `{{adset.id}}`, `{{ad.id}}` macros), Tab, read it back with JS, Publish. Leave the separate "URL parameters" field empty if the URL already has the UTMs, or use only one of the two, never both.
- **Publish:** find the Publish button and click by reference (coordinates drift when the nav expands). Success is a return to the table with an "ad updated" toast. Delivery shows "Processing" or "In review" for a while.
- **Replace media:** Media card "+" > Upload > capture the hidden file input (see `browser.md`) > upload the exact file from the launch plan (4:5 for feed, 9:16 for Stories and Reels) > select it and deselect the old one.
- **New video ad from an existing ad:** select the ad > Duplicate > Quick duplicate > in the editor rename, swap media to the video, step through text, creative generation (select nothing), enhancements (switch everything off), Destination URL, Publish.

## Settings to check (and keep off unless the user chose them)

- Advantage+ creative enhancements, including auto music, text variations, image expansion and brightness edits. Duplicating an ad often turns these back on.
- Site summaries and similar extensions that write text for you.
- Advantage+ placements if the creative only fits some placements.
- Automatic budget increases or "budget scheduling" the user did not ask for.

## Pixel and conversions

Events Manager > your dataset (pixel). Check the pixel fires on the landing page and the conversion page (the Test events tab shows live hits). Pick the optimization event in the ad set. Conversions API (server events) improves match rates; ask the user's developer to set it up rather than doing it in the browser. See `tracking.md`.

## Reading performance

- Ads table columns: Results, Reach, Impressions, Frequency, Amount spent, Cost per result, CTR (link click-through rate), CPC (cost per link click).
- Compare with analytics visits per `utm_content`. `fbclid` in the landing URL also marks Meta traffic.
- Meta often delivers cheap clicks that do not convert. Treat it as an awareness and retargeting channel until your analytics shows conversions with `utm_source=meta`.

## Traps

- Renaming an ad in the editor does not always stick. Names are cosmetic; `utm_content` is the key.
- Duplicates re-enable enhancements and extensions. Switch them off before publishing.
- A changed creative with an unchanged Website URL keeps sending the old `utm_content`. Change both.
- Editing an active ad can send it back to review and reset learning. Batch edits.
