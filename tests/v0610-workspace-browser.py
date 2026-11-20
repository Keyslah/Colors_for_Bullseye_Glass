"""Purpose: verify compact workspaces and real multi-color selection, moves and deletion.
Setup: Python Playwright with Chromium; run from any working directory.
Writes: disposable extension storage and test-results/v0610-workspace screenshots/report.
Constraints: no personal browser/session; external requests are local fixtures and
website cart mutations are blocked. CHROMIUM_EXECUTABLE can select a local browser.
"""
import json
import os
import shutil
import tempfile
import traceback
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / 'extension'
OUT = ROOT / 'test-results'
OUT.mkdir(exist_ok=True)
checks, errors = [], []
page = None
failure = None


def passed(message):
    checks.append(message)
    print('PASS:', message, flush=True)


def fixture(route):
    if route.request.method != 'GET':
        raise AssertionError('No website cart mutations belong in a workspace test')
    if route.request.resource_type == 'image':
        route.fulfill(status=200, content_type='image/svg+xml',
                      body='<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160"><rect width="160" height="160" fill="#dce3db"/></svg>')
    else:
        route.fulfill(status=200, content_type='text/html', body='<html><body>Isolated fixture</body></html>')


def workspace(current, predicate='true'):
    return current.evaluate('''async () => {
      const match=value=>value && (''' + predicate + ''');
      const read=async()=>(await chrome.storage.local.get('bullseyeProjectV1')).bullseyeProjectV1;
      const value=await read();if(match(value))return value;
      return new Promise((resolve,reject)=>{
        const finish=value=>{if(!match(value))return;clearTimeout(timer);chrome.storage.onChanged.removeListener(listener);resolve(value);};
        const listener=(changes,area)=>{if(area==='local' && changes.bullseyeProjectV1)finish(changes.bullseyeProjectV1.newValue);};
        const timer=setTimeout(()=>{chrome.storage.onChanged.removeListener(listener);reject(new Error('Workspace save did not arrive'));},15000);
        chrome.storage.onChanged.addListener(listener);read().then(finish,reject);
      });
    }''')


def card(current, target):
    return current.locator(f'#product-grid > [data-target-id="{target}"]')


def order(current, expected):
    current.wait_for_function('expected => JSON.stringify([...document.querySelectorAll("#product-grid > [data-target-id]")].map(el=>el.dataset.targetId))===JSON.stringify(expected)', arg=expected)
    assert current.locator('#product-grid .glass-target-badge').all_inner_texts() == [str(i + 1) for i in range(len(expected))]
    dots = current.locator('#image-points > .source-point').evaluate_all('(nodes)=>Object.fromEntries(nodes.map(n=>[n.dataset.targetId,n.textContent]))')
    assert dots == {target: str(i + 1) for i, target in enumerate(expected)}


def selected(current, expected):
    current.wait_for_function('expected => JSON.stringify([...document.querySelectorAll("#product-grid > .is-palette-selected")].map(el=>el.dataset.targetId))===JSON.stringify(expected)', arg=expected)
    assert current.locator('#product-grid > [aria-selected="true"]').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.targetId)') == expected


def preserve(record):
    keys = ['sourceDataUrl', 'glassTypes', 'includeTints', 'chosenMatches', 'selectedForms', 'selectedVariants', 'quantities', 'selection']
    value = {key: record.get(key) for key in keys}
    value['targets'] = {target['id']: target for target in record['targets']}
    value['cart'] = {item['key']: item for item in record['cart']}
    return value


def same_row(left, right, tolerance=3):
    a, b = left.bounding_box(), right.bounding_box()
    assert a and b
    assert abs(a['y'] + a['height'] / 2 - b['y'] - b['height'] / 2) <= tolerance, (a, b)


try:
    with sync_playwright() as playwright:
        executable = os.environ.get('CHROMIUM_EXECUTABLE')
        if not executable and not Path(playwright.chromium.executable_path).exists():
            executable = shutil.which('chromium') or shutil.which('google-chrome')
        browser_options = {'executable_path': executable} if executable else {'channel': 'chromium'}
        for orientation in ['portrait', 'landscape']:
            with tempfile.TemporaryDirectory() as profile:
                context = playwright.chromium.launch_persistent_context(profile, headless=True,
                    viewport={'width':1440, 'height':1000}, **browser_options,
                    args=[f'--disable-extensions-except={EXT}', f'--load-extension={EXT}'])
                context.route('https://**/*', fixture)
                context.route('http://**/*', fixture)
                worker = context.service_workers[0] if context.service_workers else context.wait_for_event('serviceworker')
                worker.evaluate("() => { globalThis.fetch=async()=>{throw new Error('External worker fetch blocked in compact workspace fixture');}; }")
                origin = f'chrome-extension://{worker.url.split("/")[2]}'
                page = context.new_page()
                page.set_default_timeout(15000)
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(origin + '/manifest.json')
                page.evaluate('''async orientation => {
                  const catalog=await (await fetch('./data/catalog.json')).json();
                  const formats=await (await fetch('./data/product-formats.json')).json();
                  const {productForForm}=await import('./lib/product-formats.js');
                  const ids=['green','red','orange','coral','purple'],hexes=['#287850','#96202D','#E88128','#D17E96','#75128B'];
                  const productIds=['001426','001122','001125','001305','001128'];
                  const canvas=document.createElement('canvas');
                  canvas.width=orientation==='portrait'?420:840;canvas.height=orientation==='portrait'?700:420;
                  const ctx=canvas.getContext('2d');
                  hexes.forEach((hex,i)=>{ctx.fillStyle=hex;ctx.fillRect(i*canvas.width/5,0,canvas.width/5,canvas.height);});
                  const selectedForms={[productIds[1]]:'fine'},selectedVariants={},quantities={};
                  productIds.forEach((id,index)=>{
                    const product=productForForm(catalog.products.find(p=>p.id===id),formats,selectedForms[id]||'medium');
                    const variant=product.variants.find(v=>v.available)||product.variants[0];
                    selectedVariants[id]=String(variant.id);quantities[`${id}:${variant.id}`]=index+2;
                  });
                  await chrome.storage.local.set({bullseyeProjectV1:{version:6,photoGuideVersion:1,
                    sourceName:`${orientation} compact fixture`,sourceDataUrl:canvas.toDataURL(),
                    targets:ids.map((id,i)=>({id,rgb:hexes[i].match(/[0-9a-f]{2}/gi).map(v=>parseInt(v,16)),manual:true,custom:true,x:(i+.5)/5,y:.5})),
                    activeTargetId:'green',format:'medium',preferredJarSize:'5lb',imageSize:'larger',
                    glassTypes:{transparent:true,opalescent:true},includeTints:false,view:'palette',
                    chosenMatches:Object.fromEntries(ids.map((id,i)=>[id,productIds[i]])),selectedForms,selectedVariants,quantities}});
                }''', orientation)
                page.goto(origin + '/picker.html?workspace=1')
                expect(page.locator('#image-loaded')).to_be_visible()
                order(page, ['green', 'red', 'orange', 'coral', 'purple'])
                workspace(page, 'value.targets.length===5 && !!value.targets[0].lab')
                for identifier in ['account-menu','about-menu','palette-tab','library-tab','glass-search','palette-chips','open-color-editor','show-alternatives']:
                    assert page.locator('#' + identifier).count() == 0, identifier
                same_row(page.locator('#remix-palette'), page.locator('#thickness-reference'))
                same_row(page.locator('#open-cart'), page.locator('#close-picker'))
                assert page.locator('#close-picker').bounding_box()['x'] > page.locator('#open-cart').bounding_box()['x']
                first = card(page, 'green')
                assert first.locator('.delete-target').bounding_box()['y'] < first.locator('.row-alternatives').bounding_box()['y']
                passed(f'{orientation}: removed controls stay absent; thickness, Cart and close button use requested rows; Delete sits above Alternatives')

                card(page, 'red').locator('.glass-checkbox').uncheck()
                before = workspace(page, "value.selection.excludedTargetIds.includes('red')")
                preserved = preserve(before)
                card(page, 'red').locator('.palette-reorder-handle').click()
                card(page, 'coral').locator('.photo-button').click(modifiers=['Shift'])
                selected(page, ['red', 'orange', 'coral'])
                expect(page.locator('#detail-dialog')).not_to_be_visible()
                assert preserve(workspace(page)) == preserved
                expect(card(page, 'red').locator('.glass-checkbox')).not_to_be_checked()
                passed(f'{orientation}: Shift-click selects a range with visible/accessible state and leaves glass checks, photos and purchase data alone')

                destination = card(page, 'purple')
                bounds = destination.bounding_box()
                position = {'x':bounds['width'] - 3 if orientation == 'landscape' else bounds['width'] / 2,
                            'y':bounds['height'] / 2 if orientation == 'landscape' else bounds['height'] - 3}
                card(page, 'orange').locator('.palette-reorder-handle').drag_to(destination, target_position=position)
                expected = ['green', 'purple', 'red', 'orange', 'coral']
                order(page, expected)
                selected(page, ['red', 'orange', 'coral'])
                after = workspace(page, "value.targets[1].id==='purple'")
                assert preserve(after) == preserved
                page.screenshot(path=str(OUT / f'v0610-main-{orientation}.png'), full_page=True)
                passed(f'{orientation}: dragging a selected grip moves the complete range in order and preserves colors, variants, quantities and exclusions')

                # A real input, an open dialog and an editable field must keep
                # ordinary text-editing Delete/Backspace behavior.
                card(page, 'green').locator('.purchase-toggle').click()
                quantity = card(page, 'green').locator('.quantity-field')
                quantity.fill('32')
                quantity.press('Backspace')
                assert len(page.locator('#product-grid > [data-target-id]').all()) == 5
                quantity.fill(str(before['cart'][0]['quantity']))
                quantity.press('Tab')
                card(page, 'green').get_by_role('button', name='Close purchase options').click()
                card(page, 'green').locator('.row-alternatives').click()
                page.locator('#alternatives-search').fill('Blue')
                page.locator('#alternatives-search').press('Backspace')
                page.locator('#alternatives-title').click()
                page.keyboard.press('Delete')
                assert page.locator('#product-grid > [data-target-id]').count() == 5
                page.locator('#close-alternatives').click()
                passed(f'{orientation}: Backspace edits an input and Delete inside Alternatives never deletes palette colors')

                card(page, 'red').locator('.palette-reorder-handle').click()
                card(page, 'coral').locator('.palette-reorder-handle').click(modifiers=['Shift'])
                selected(page, ['red', 'orange', 'coral'])
                card(page, 'coral').locator('.palette-reorder-handle').press('Delete')
                order(page, ['green', 'purple'])
                # Reload before waiting for the save debounce. The pagehide
                # worker handoff must retain the final edit.
                page.reload()
                expect(page.locator('#image-loaded')).to_be_visible()
                order(page, ['green', 'purple'])
                deleted = workspace(page, 'value.targets.length===2')
                assert set(deleted['chosenMatches']) == {'green', 'purple'}
                assert set(deleted['selection']['targetKeys']) <= {'green', 'purple'}
                assert deleted['selection']['excludedTargetIds'] == []
                passed(f'{orientation}: Delete removes only selected swatches, cleans their ownership, renumbers source dots and survives reload')

                card(page, 'green').locator('.palette-reorder-handle').click()
                card(page, 'purple').locator('.delete-target').click()
                order(page, ['green'])
                card(page, 'green').locator('.palette-reorder-handle').click()
                card(page, 'green').locator('.palette-reorder-handle').press('Backspace')
                order(page, [])
                assert workspace(page, 'value.targets.length===0')['cart'] == []
                page.reload()
                expect(page.locator('#product-grid > [data-target-id]')).to_have_count(0)
                passed(f'{orientation}: per-card Delete immediately removes its own swatch; Backspace can remove the final selected color without restoring the catalog')

                if orientation == 'landscape':
                    # Cart presentation uses synthetic items independent of the
                    # palette; editing it must not resurrect deleted targets.
                    page.evaluate('''async () => {
                      const catalog=await (await fetch('./data/catalog.json')).json(),formats=await (await fetch('./data/product-formats.json')).json();
                      const ids=['001426','001122','001125','001305','001128','000141'];
                      const items=ids.map((id,i)=>{
                        const product=catalog.products.find(p=>p.id===id),form=['medium','fine','coarse'][i%3];
                        const variant=formats.products[id][form].variants.find(v=>v.available)||formats.products[id][form].variants[0];
                        return {productId:id,variantId:variant.id,quantity:i+1,form,name:product.name,sku:variant.sku,title:variant.title,price:variant.price,available:variant.available};
                      });
                      await (await import('./lib/working-cart.js')).saveWorkingCart({name:'Compact cart fixture',items,dirty:true});
                    }''')
                    cart_page = context.new_page()
                    cart_page.on('pageerror', lambda error: errors.append(str(error)))
                    cart_page.goto(origin + '/picker.html?workspace=1&cart=1')
                    rows = cart_page.locator('#saved-cart-items .saved-cart-item')
                    expect(rows).to_have_count(6)
                    expect(cart_page.locator('#cart-single-column')).not_to_be_checked()
                    positions = rows.evaluate_all('(nodes)=>nodes.map(n=>({x:n.getBoundingClientRect().x,y:n.getBoundingClientRect().y}))')
                    assert positions[0]['x'] != positions[1]['x'] and abs(positions[0]['y'] - positions[1]['y']) < 2, positions
                    for identifier in ['close-cart-editor','saved-cart-name','save-cart-draft','duplicate-cart-draft','open-saved-carts']:
                        same_row(cart_page.locator('#copy-website-cart'), cart_page.locator('#' + identifier), 4)
                    assert cart_page.locator('#close-cart-editor').bounding_box()['x'] < cart_page.locator('#copy-website-cart').bounding_box()['x']
                    assert cart_page.locator('#saved-cart-name').bounding_box()['width'] < 240
                    first = rows.first
                    heading, photo = first.locator('.saved-cart-item-heading'), first.locator('.saved-cart-photo')
                    assert heading.bounding_box()['y'] + heading.bounding_box()['height'] <= photo.bounding_box()['y'] + 2
                    grade, size, quantity = [first.locator(selector).bounding_box() for selector in ['.cart-grade-select','.cart-size-select','.quantity-field']]
                    assert grade['x'] >= photo.bounding_box()['x'] + photo.bounding_box()['width'] - 2
                    assert grade['y'] < size['y'] < quantity['y']
                    same_row(heading.locator('h3'), heading.locator('.cart-item-price'), 4)
                    assert 'Cart kept automatically' not in cart_page.locator('body').inner_text()
                    assert 'Photo guide:' not in cart_page.locator('body').inner_text()
                    assert cart_page.locator('.cart-send-note').count() == 0
                    cart_page.screenshot(path=str(OUT / 'v0610-cart-grid.png'), full_page=True)
                    passed('Cart uses compact multi-column boxes with name/price above photo, three small input rows beside it and inline cart actions')

                    original_cart = cart_page.evaluate("async()=>(await chrome.storage.local.get('bullseyeWorkingCartV1')).bullseyeWorkingCartV1.items")
                    cart_page.locator('#cart-single-column').check()
                    positions = rows.evaluate_all('(nodes)=>nodes.map(n=>({x:n.getBoundingClientRect().x,y:n.getBoundingClientRect().y}))')
                    assert len({position['x'] for position in positions}) == 1
                    cart_page.reload()
                    expect(cart_page.locator('#cart-single-column')).to_be_checked()
                    expect(rows).to_have_count(6)
                    assert cart_page.evaluate("async()=>(await chrome.storage.local.get('bullseyeWorkingCartV1')).bullseyeWorkingCartV1.items") == original_cart
                    cart_page.locator('#cart-single-column').uncheck()
                    passed('Single-column checkbox changes layout, survives reload and leaves every cart item and quantity intact')

                    cart_page.locator('#open-cart-add').click()
                    expect(cart_page.locator('#cart-add-dialog')).to_be_visible()
                    colors = cart_page.locator('#cart-color-filters')
                    expect(colors.locator('button[data-color-family="blue"]')).to_be_visible()
                    colors.locator('button[data-color-family="blue"]').click()
                    expect(colors.locator('button[data-color-family="blue"]')).to_have_attribute('aria-pressed', 'true')
                    expect(cart_page.locator('#saved-cart-search-results [data-product-id="001108"]')).to_be_visible()
                    expect(cart_page.locator('#saved-cart-search-results [data-product-id="001122"]')).to_have_count(0)
                    cart_page.locator('#saved-cart-search').fill('001108')
                    expect(cart_page.locator('#saved-cart-search-results .saved-cart-search-result')).to_have_count(1)
                    cart_page.locator('#saved-cart-search').fill('')
                    colors.locator('button[data-color-family="red"]').click()
                    expect(cart_page.locator('#saved-cart-search-results [data-product-id="001122"]')).to_be_visible()
                    expect(cart_page.locator('#saved-cart-search-results [data-product-id="001108"]')).to_have_count(0)
                    cart_page.screenshot(path=str(OUT / 'v0610-add-colors.png'), full_page=True)
                    passed('Major color buttons filter Add Colors and combine with text search without changing cart or palette')
                    cart_page.locator('#done-cart-add').click()
                    assert workspace(page)['targets'] == []
                    cart_page.set_viewport_size({'width':390,'height':844})
                    assert cart_page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    passed('Narrow cart viewport stays within the window')
                    cart_page.close()
                context.close()
        assert not errors, errors
        passed('No uncaught browser errors')
except Exception as error:
    failure = traceback.format_exc()
    print(failure, flush=True)
    if page and not page.is_closed():
        try:
            page.screenshot(path=str(OUT / 'v0610-failure.png'), full_page=True)
        except Exception:
            pass
    raise
finally:
    (OUT / 'v0610-workspace-report.json').write_text(json.dumps({'checks':checks,'errors':errors,'failure':failure},indent=2))
