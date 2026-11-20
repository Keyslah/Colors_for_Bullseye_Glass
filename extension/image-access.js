/**
 * Purpose: request access to the pending photo host from a visible permission window.
 * Setup: opened by the extension worker; the pending image is held in session storage.
 * Destructive behavior: none; grants only the displayed image origin after a user click.
 * Constraints: Chrome permission prompts require the click gesture; stale photos never replace newer choices.
 */
import {getPendingImage, requestImageAccess} from './lib/extension.js';

const grant = document.getElementById('grant-image-access');
const host = document.getElementById('access-host');
const status = document.getElementById('access-status');
const description = document.getElementById('access-description');
let pending = null, requesting = false;

function renderPending(value) {
  pending = value;
  if (!pending || pending.dataUrl) { window.close(); return; }
  let hostname = '';
  try { hostname = new URL(pending.sourceUrl).hostname; } catch { /* A newer image may still be resolving. */ }
  host.textContent = hostname;
  grant.disabled = requesting || !pending.needsPermission;
  grant.textContent = requesting ? 'Opening image…' : 'Allow image access';
  description.textContent = pending.loading ? 'Loading your selected photo…' : 'Allow this image host so your photo can open in the palette.';
  status.textContent = pending.error && !pending.needsPermission ? pending.error : '';
}

grant.addEventListener('click', async () => {
  if (!pending?.needsPermission || requesting) return;
  const requested = pending;
  requesting = true; renderPending(pending);
  try {
    // Keep this call within the click; do not await another task before requesting.
    const result = await requestImageAccess(requested.sourceUrl, requested.updatedAt);
    if (result?.dataUrl) { window.close(); return; }
  } catch (error) {
    if (pending?.updatedAt === requested.updatedAt) status.textContent = error.message || 'Image access was not granted.';
  } finally {
    requesting = false;
    grant.disabled = !pending?.needsPermission;
    grant.textContent = 'Allow image access';
  }
});
document.getElementById('cancel-image-access').addEventListener('click', () => window.close());
document.addEventListener('keydown', event => { if (event.key === 'Escape') window.close(); });
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'session' && Object.hasOwn(changes, 'pendingImage')) renderPending(changes.pendingImage.newValue);
});
renderPending(await getPendingImage());
if (!grant.disabled) grant.focus();
