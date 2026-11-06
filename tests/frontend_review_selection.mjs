import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source = await readFile(new URL('../static/review-selection.js', import.meta.url), 'utf8');
const {matchesItem, selectionKey, selectedItemKeys, isOnMap} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));

const items = [
    ...Array.from({length: 40}, (_, i) => ({component: 'overlays', key: `id:${i}`, name: i === 0 ? 'Coëfficiënt hittestress' : `Overlay ${i}`, detail: 'berekend', checked: true, spatial: false})),
    {component: 'indicators', key: 'id:1', name: 'Gezondheid', checked: true, spatial: false},
    {component: 'indicators', key: 'id:2', name: 'Mobiliteit', checked: false, spatial: false},
    {component: 'measures', key: 'id:1', name: 'Park', checked: false, spatial: true},
    {component: 'alerts', key: 'id:1', name: 'Hittestress', checked: true, spatial: true},
    {component: 'alerts', key: 'id:2', name: 'Verkeer', checked: false, spatial: false}
];
const defaults = {query: '', component: 'all', selection: 'all', spatialOnly: false};
const find = overrides => items.filter(item => matchesItem(item, {...defaults, ...overrides}, item.checked));
assert.equal(find({}).length, 45);
assert.equal(find({component: 'alerts'}).length, 2);
assert.equal(find({query: ' COEFFICIENT '})[0].key, 'id:0');
assert.equal(find({query: 'does not exist'}).length, 0);
assert.equal(find({selection: 'unselected'}).length, 3);
assert.equal(find({spatialOnly: true}).length, 2);
assert.equal(find({component: 'overlays', query: 'hittestress'}).length, 1);
assert.equal(find({component: 'alerts', selection: 'selected', spatialOnly: true}).length, 1);
assert.equal(isOnMap({component: 'overlays', spatial: true}), false);

// Bulk selection only applies to the current results, preserving other records.
const result = new Set(find({component: 'overlays', query: 'hittestress'}));
items.forEach(item => { if (result.has(item)) item.checked = false; });
assert.equal(items.filter(item => item.component === 'overlays' && item.checked).length, 39);
assert.equal(items.find(item => item.component === 'alerts' && item.key === 'id:1').checked, true);
// Equal Tygron IDs in different components must not reselect an excluded map object.
const keys = selectedItemKeys(items);
assert.equal(keys.has(selectionKey('overlays', 'id:1')), true);
assert.equal(keys.has(selectionKey('measures', 'id:1')), false);
assert.equal(keys.has(selectionKey('alerts', 'id:1')), true);
assert.equal(keys.size, items.filter(item => item.checked).length);
console.log('45 items: type/text/selection/map filters, scoped bulk selection and duplicate IDs pass.');
