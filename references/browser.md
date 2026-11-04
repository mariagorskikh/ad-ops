# Driving ad platforms from a browser automation tool

Ad managers are heavy single-page apps. These habits prevent most mis-clicks. They apply to any browser tool that offers screenshots, element references, typing and JavaScript.

## Clicking

- **Prefer element references over coordinates.** Find the element (by text or role), then click by reference. References survive scrolling and layout shifts; coordinates do not.
- **Screenshot pixels are not CSS pixels.** If you compute a position in JavaScript, scale it by screenshot width divided by `window.innerWidth`.
- **Re-screenshot after any layout change.** Side navs that expand on hover (Meta does this) shift everything. Move the mouse away from the nav to collapse it.
- **Batch only predictable steps.** A batch that stops on the first error is fine; a batch that keeps clicking after a dialog opened is not.

## Typing

- Typing goes to the focused element. Focus first (click by reference, or `el.focus(); el.select()` in JS), then select all, type, press Tab.
- Read the value back with JS before saving (`input.value.includes('spring-hero-01')`). If the tool redacts query strings in JS output, return a boolean or a length instead of the string.
- Select-all with nothing focused selects the whole page. Always focus first.
- Rich text fields (Meta primary text) are `contenteditable` DIVs, not inputs. Click into them, select all, type.

## Hidden and lazy content

- Some editor sections render only after you scroll the panel once or wait 10 to 15 seconds.
- Some inputs sit inside `display:none` cards (Meta's Destination card in the standalone ad editor has been one). Walk up from the input, set `style.display='block'` on hidden ancestors, then `scrollIntoView({block:'center'})`.
- Virtualized tables (Google, X) drop off-screen rows from the DOM. Page text extraction misses them. Screenshot, scroll, or filter `document.body.innerText` with a regex.

## File uploads

- Upload buttons often open a hidden `input[type=file]`. Patch `HTMLInputElement.prototype.click` to capture the input when the button is clicked, then hand that input to the tool's file upload.
- Shadow DOM pages (YouTube Studio is one) hide the input from normal search. Walk shadow roots in JS to find it, give it an id and label, make it visible in place (do not move it out of its shadow root; moved inputs stop working), then upload.
- Video uploads fail more often than images. If a video does not register after two tries, say so and hand it to the user.

## Saving and verifying

- Every section may have its own Save. "Done" in a wizard step often saves nothing.
- After a save, check the network log for the mutation request and its status, then reload and read the table.
- After clicking a tracked link, the analytics request in the network log shows which UTMs the site received.

## Stop and hand over

- Any re-auth, password, 2FA or "Confirm it's you" prompt. Popups for these are often blocked for automation anyway.
- Any payment, billing or tax form.
- A page that stays blank or returns 403 after two tries ten minutes apart. Check the logged-in account first. Clearing the service worker and caches (`navigator.serviceWorker.getRegistrations()` then `unregister()`, `caches.keys()` then `caches.delete`) can fix a stuck shell, but never fixes a permissions problem.
