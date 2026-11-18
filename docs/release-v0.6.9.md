# Colors for Bullseye Glass v0.6.9

## One name

The extension is named **Colors for Bullseye Glass** in Chrome's extension list, the toolbar button, the side panel, page titles and the About menu. The installable file is `Colors-for-Bullseye-Glass-v0.6.9.zip`.

## Larger thickness reference

The palette bar shows **100% thickness = 6 mm solid glass = 16 mm fine frit \*Rough estimate** in much larger text (20 px instead of 11 px). When it does not fit beside the palette buttons, it moves to its own row and wraps on narrow panels.

## Backups

**Back up my data** saves `Colors-for-Bullseye-Glass-personal-data-<date>.json`. **Restore my data** accepts backups made by v0.6.9 or later, so make a fresh backup after updating.

## Update while keeping your personal data

1. Close picker and cart tabs.
2. Extract `Colors-for-Bullseye-Glass-v0.6.9.zip` into the **same installed extension folder**, replacing its files. If Chrome loads the repository's `extension` subfolder, replace the files inside that subfolder.
3. Open `chrome://extensions`, click **Reload** on Colors for Bullseye Glass and confirm **0.6.9**.
4. Reopen the picker/cart. Refresh existing source-image pages before using their right-click image command.

Settings, palettes, photos and carts are kept. Storage keys and databases are unchanged.

## Verification

All **259 JavaScript tests** pass. The release gate runs manifest/catalog/module checks and the native workspace, layout, matching, cart, unavailable-selection, Prominence, reordering, navigation and personal-data browser tests. The layout test checks that the full new reference text is visible and fits at widths from 320 to 1440 px. Store mutations use disposable fixtures, with no customer account or live cart.

The installable ZIP contains **185 exact-source files**. The release workflow verifies it against the tested source before publication, then downloads the published archive and repeats the same check. Matching, catalog photographs, color samples and thickness calculations are unchanged.
