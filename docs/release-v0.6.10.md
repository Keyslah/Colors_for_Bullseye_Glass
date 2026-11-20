# Colors for Bullseye Glass v0.6.10

## Main picker

- Removed the Account and information menus, Matches/All glass row, numbered toolbar swatches, Edit color button, and global Alternatives button.
- The picker shows its matches directly. Remix and the thickness reference share a row when space allows, with responsive wrapping in narrow side panels.
- The close X sits immediately after Cart and saves pending changes before closing the picker.
- Sign in remains available; a confirmed login displays **Signed in**.
- Each color has **Delete** directly above **Alternatives**. Delete removes that color immediately.
- Click a color card or grip, then Shift-click to select a range. Ctrl/Command-click toggles individual colors. Drag a selected grip to move the selected colors together.
- Delete/Backspace removes selected colors while text fields, purchase controls and open dialogs keep their normal editing behavior. Deleting the last color remains empty after reload.

## Image access

An image that needs host access automatically opens a focused, separate **Allow image access** window. The window identifies the host and has a prominent permission button. Repeated requests reuse the window; the picker button reopens it after dismissal. A cancelled or superseded request cannot replace a newer photo.

## Cart and Add Colors

- Back, Copy my Bullseye cart, View Bullseye cart, Duplicate, Saved Carts, cart name and Save cart share the cart toolbar. The name field is approximately 20 characters wide and retains longer names.
- **Cart items**, **Add Colors** and **Single column** are grouped on the left.
- Cart items use a grid by default. Each compact box places its name and price above the photo, with grade, size and quantity stacked beside the image.
- Single-column mode persists through reloads.
- Removed the photo-guide text, repeated-send explanation and automatic-cart-status message.
- Add Colors has Bullseye's major family filters beside its heading: Red, Orange, Yellow, Green, Blue-Green, Blue, Purple & Violet, Black, Gray, White & Clear, Neutrals and Pink.

Matching calculations, catalog photographs, purchase variants, storage keys for palettes and carts, and explicit website-cart sending remain intact.

## Update an existing installation

1. Close picker and cart tabs.
2. Extract `Colors-for-Bullseye-Glass-v0.6.10.zip` into the **same installed extension folder**, replacing its files. If Chrome loads the repository's `extension` subfolder, replace the files inside that subfolder.
3. Open `chrome://extensions`, click **Reload** on Colors for Bullseye Glass, and confirm version **0.6.10**.
4. Reopen the picker/cart. Refresh any source-image pages before using the right-click image command.

Keep the existing Chrome installation and folder to preserve saved settings, palettes, photos and carts.

## Verification

All **268 JavaScript regression tests** passed, together with native Chromium checks for the new layout and retained behavior. The installable ZIP contains **191 files**, each checked byte-for-byte against the tested source.

The release gate runs JavaScript regression tests, manifest/catalog/module checks, native Chromium tests for the new controls, selection, cart layouts, permission popup and retained cart/backup behavior, and an exact-source ZIP integrity check. Browser checks use disposable profiles and store fixtures. The permission response is a controlled fixture; popup creation, foreground focus, user-click activation, image decoding and storage handoff use native Chromium APIs. The published ZIP is downloaded and checked against the tested source again.
