/**
 * Purpose: keep every reviewed glass discoverable through the Add Colors families.
 * Setup: node --test; reads the bundled catalog and independent family filter.
 * Destructive behavior: none; tests never write data or contact the store.
 * Constraints: validates category membership only, not photo matching or stock.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {CART_COLOR_FAMILIES, inCartColorFamily} from '../extension/lib/cart-color-families.js';

const catalog = JSON.parse(readFileSync(new URL('../extension/data/catalog.json', import.meta.url), 'utf8')).products;
const clear = JSON.parse(readFileSync(new URL('../extension/data/clear-cart.json', import.meta.url), 'utf8')).products;
const product = id => {
  const value = catalog.find(entry => entry.id === id);
  assert.ok(value, `Missing reviewed fixture ${id}`);
  return value;
};

test('every reviewed catalog color is discoverable in a specific family and All', () => {
  const families = CART_COLOR_FAMILIES.filter(family => family.id !== 'all');
  for (const entry of catalog) {
    assert.ok(inCartColorFamily(entry), `${entry.name} must appear under All`);
    assert.ok(families.some(family => inCartColorFamily(entry, family.id)), `${entry.name} has no color family`);
  }
});

test('manufacturer overlaps retain aquamarines in Blue and Blue-Green without admitting red glass', () => {
  const aquamarine = product('001108'), red = product('001122');
  assert.equal(inCartColorFamily(aquamarine, 'blue'), true);
  assert.equal(inCartColorFamily(aquamarine, 'blue-green'), true);
  assert.equal(inCartColorFamily(aquamarine, 'red'), false);
  assert.equal(inCartColorFamily(red, 'red'), true);
  assert.equal(inCartColorFamily(red, 'blue'), false);
  assert.equal(inCartColorFamily(red, 'blue-green'), false);
});

test('names without a literal family word keep their intended categories', () => {
  assert.equal(inCartColorFamily(product('000131'), 'green'), true); // Artichoke
  assert.equal(inCartColorFamily(product('000303'), 'purple'), true); // Dusty Lilac
  assert.equal(inCartColorFamily(product('000119'), 'gray'), true); // Mink
  assert.equal(inCartColorFamily(product('000119'), 'neutral-brown'), true);
  assert.equal(inCartColorFamily(product('000102'), 'black'), true); // Blue Black
  assert.equal(inCartColorFamily(product('000100'), 'gray'), false);
  assert.equal(inCartColorFamily(product('000301'), 'pink'), true);
});

test('clear cart products stay in White & Clear and unknown families never match', () => {
  assert.ok(clear.length, 'The separate clear cart catalog must be present');
  for (const entry of clear) {
    assert.equal(inCartColorFamily(entry, 'white'), true);
    assert.equal(inCartColorFamily(entry, 'blue'), false);
    assert.equal(inCartColorFamily(entry, 'not-a-family'), false);
  }
  assert.equal(inCartColorFamily(product('001108'), 'not-a-family'), false);
  assert.equal(inCartColorFamily({id:'unknown-style'}, 'red'), false);
});
