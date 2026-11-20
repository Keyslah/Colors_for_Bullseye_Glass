"""Purpose: verify the focused image-access popup and picker close in native Chromium.
Setup: Python Playwright and Chromium; no existing browser profile is used.
Writes: disposable extension storage and test-results/v0610-image-access artifacts.
Constraints: external requests are blocked; permission responses are controlled fixtures,
while popup windows, click gestures, image decoding and extension storage are real.
"""
import base64
import io
import json
import os
import shutil
import tempfile
import traceback
from pathlib import Path

from PIL import Image
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / 'extension'
OUT = ROOT / 'test-results'
OUT.mkdir(exist_ok=True)
checks, errors = [], []
failure = None
page = None


def passed(message):
    checks.append(message)
    print('PASS:', message, flush=True)


try:
    data = io.BytesIO()
    Image.new('RGB', (360, 240), '#569376').save(data, format='PNG')
    encoded = base64.b64encode(data.getvalue()).decode()
    with sync_playwright() as playwright, tempfile.TemporaryDirectory() as profile:
        executable = os.environ.get('CHROMIUM_EXECUTABLE')
        if not executable and not Path(playwright.chromium.executable_path).exists():
            executable = shutil.which('chromium') or shutil.which('google-chrome')
        browser_options = {'executable_path': executable} if executable else {'channel': 'chromium'}
        context = playwright.chromium.launch_persistent_context(profile, headless=True,
            no_viewport=True, **browser_options,
            args=['--window-size=1280,900', f'--disable-extensions-except={EXT}', f'--load-extension={EXT}'])
        context.route('http://**/*', lambda route: route.abort())
        context.route('https://**/*', lambda route: route.abort())
        worker = context.service_workers[0] if context.service_workers else context.wait_for_event('serviceworker')
        worker.evaluate('''encoded => {
          globalThis.fetch=async url=>{
            if(String(url)==='https://photos.example/art.png')return new Response(Uint8Array.from(atob(encoded),c=>c.charCodeAt(0)),{headers:{'content-type':'image/png'}});
            throw new Error('External requests blocked in permission fixture');
          };
        }''', encoded)
        origin = f'chrome-extension://{worker.url.split("/")[2]}'
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(origin + '/manifest.json')
        page.evaluate('''async () => {
          const canvas=document.createElement('canvas');canvas.width=420;canvas.height=640;
          const ctx=canvas.getContext('2d');ctx.fillStyle='#9a4069';ctx.fillRect(0,0,420,640);
          await chrome.storage.local.set({bullseyeProjectV1:{version:6,photoGuideVersion:1,
            sourceName:'Existing photo',sourceDataUrl:canvas.toDataURL(),targets:[{id:'old',rgb:[154,64,105],manual:true,x:.5,y:.5}],
            activeTargetId:'old',format:'medium',glassTypes:{transparent:true,opalescent:true},view:'palette'}});
        }''')
        page.goto(origin + '/picker.html?workspace=1')
        expect(page.locator('#image-loaded')).to_be_visible()
        with context.expect_page() as opening:
            page.evaluate('''async () => chrome.storage.session.set({pendingImage:{sourceUrl:'https://photos.example/art.png',
              needsPermission:true,error:'Host access needed',updatedAt:Date.now()}})''')
        popup = opening.value
        popup.on('pageerror', lambda error: errors.append(str(error)))
        popup.wait_for_url(origin + '/image-access.html')
        expect(popup.locator('#grant-image-access')).to_be_visible()
        expect(popup.locator('#grant-image-access')).to_be_enabled()
        expect(popup.locator('#access-host')).to_have_text('photos.example')
        window_info = popup.evaluate('async()=>{const w=await chrome.windows.getCurrent();return {id:w.id,type:w.type,focused:w.focused};}')
        assert window_info['type'] == 'popup'
        assert window_info['focused'] is True
        # Headless Chromium can inherit the launch viewport for new windows.
        # Also exercise a content area narrower/shorter than the requested popup.
        popup.set_viewport_size({'width':480, 'height':440})
        assert popup.evaluate('''() => ['grant-image-access','cancel-image-access'].every(id=>{
          const r=document.getElementById(id).getBoundingClientRect();return r.top>=0 && r.bottom<=innerHeight && r.left>=0 && r.right<=innerWidth;
        })'''), 'Permission actions must fit a compact popup viewport without scrolling.'
        popup.screenshot(path=str(OUT / 'v0610-image-access.png'), full_page=True)
        passed('A pending image automatically opens a visible, separate popup with its exact host and a prominent Allow image access button')

        reopened = page.evaluate('''async () => {
          const {openImageAccessWindow}=await import('./lib/extension.js');
          const {pendingImage:p}=await chrome.storage.session.get('pendingImage');
          return Promise.all([1,2,3].map(()=>openImageAccessWindow(p.sourceUrl,p.updatedAt)));
        }''')
        assert all(result['windowId'] == window_info['id'] for result in reopened)
        assert len([tab for tab in context.pages if tab.url.endswith('/image-access.html')]) == 1
        passed('Repeated permission requests focus the existing window instead of opening duplicates')

        popup.evaluate('''() => {chrome.permissions.request=async options=>{
          window.permissionAttempt={options,gesture:navigator.userActivation.isActive};return false;
        };}''')
        popup.locator('#grant-image-access').click()
        expect(popup.locator('#access-status')).to_contain_text('not granted')
        attempt = popup.evaluate('window.permissionAttempt')
        assert attempt == {'options': {'origins': ['https://photos.example/*']}, 'gesture': True}
        assert page.locator('#source-name').text_content() == 'Existing photo'
        passed('Denying permission keeps the current photo; the request is scoped to the displayed host and made within the user click')

        with popup.expect_event('close'):
            popup.locator('#cancel-image-access').click()
        with context.expect_page() as opening:
            page.locator('#allow-image-access').click()
        popup = opening.value
        popup.wait_for_url(origin + '/image-access.html')
        expect(popup.locator('#grant-image-access')).to_be_enabled()
        popup.evaluate('() => {chrome.permissions.request=async()=>true;}')
        with popup.expect_event('close'):
            popup.locator('#grant-image-access').click()
        page.wait_for_function("document.querySelector('#source-canvas').width===360 && document.querySelector('#source-canvas').height===240")
        expect(page.locator('#image-access-note')).not_to_be_visible()
        passed('The picker button reopens a dismissed popup; allowing access loads the photo in the picker and closes the popup')

        with context.expect_page() as opening:
            page.evaluate('''async () => chrome.storage.session.set({pendingImage:{sourceUrl:'https://photos.example/new.png',
              needsPermission:true,updatedAt:Date.now()+10}})''')
        popup = opening.value
        expect(popup.locator('#grant-image-access')).to_be_visible()
        with popup.expect_event('close'):
            page.evaluate("async () => (await import('./lib/extension.js')).cancelPendingImage()")
        assert page.locator('#source-canvas').evaluate('canvas=>canvas.width') == 360
        passed('Cancelling an obsolete image request closes its popup without altering the loaded photo')

        survivor = context.new_page()
        survivor.goto(origin + '/manifest.json')
        with page.expect_event('close'):
            page.locator('#close-picker').click()
        assert not survivor.is_closed()
        passed('The X closes only its own picker tab and keeps other open pages')
        assert not errors, errors
        context.close()
except Exception:
    failure = traceback.format_exc()
    print(failure, flush=True)
finally:
    (OUT / 'v0610-image-access-report.json').write_text(json.dumps({'checks':checks, 'errors':errors, 'failure':failure}, indent=2))
if failure:
    raise SystemExit(1)
