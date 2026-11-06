import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const root = new URL('../', import.meta.url);
const nl = JSON.parse(await readFile(new URL('translations/nl.json', root), 'utf8'));
const en = JSON.parse(await readFile(new URL('translations/en.json', root), 'utf8'));
const node = (text, source = false) => ({textContent: text, parentElement: {closest: () => source}});
const nodes = [node('  Review the scenario  '), node('0 of 8 spatial objects'), node('1 of 21 selected'), node('Inloggen', true), node('Use an active session →'), node('14.4 KB · ready for validation'), node('← Back to login')];
const input = {value: 'my untouched notes', attributes: {placeholder: 'Search by project name…'}, closest: () => false,
    hasAttribute(name) { return name in this.attributes; }, getAttribute(name) { return this.attributes[name]; },
    setAttribute(name, value) { this.attributes[name] = value; }};
const buttons = ['nl', 'en'].map(language => ({dataset: {language}, setAttribute(name, value) { this[name] = value; }}));
let events = 0;
globalThis.NodeFilter = {SHOW_TEXT: 4};
globalThis.CustomEvent = class {constructor(type) { this.type = type; }};
globalThis.document = {
    body: {}, documentElement: {lang: 'en'}, title: 'Log in · ScenarioDossier',
    querySelector: () => ({textContent: JSON.stringify({language: 'en', catalog: en})}),
    querySelectorAll: selector => selector === '[data-language]' ? buttons : [input],
    createTreeWalker() { let index = -1; return {nextNode() { index++; this.currentNode = nodes[index]; return index < nodes.length; }}; },
    dispatchEvent(event) { assert.equal(event.type, 'languagechange'); events++; }
};
const source = await readFile(new URL('static/i18n.js', root), 'utf8');
const i18n = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
i18n.changeLanguage('nl', nl);
assert.deepEqual(nodes.map(node => node.textContent), ['  Controleer het scenario  ', '0 van 8 ruimtelijke objecten', '1 van 21 geselecteerd', 'Inloggen', 'Een actieve sessie gebruiken →', '14.4 KB · gereed voor controle', '← Terug naar inloggen']);
assert.equal(input.attributes.placeholder, 'Zoek op projectnaam…');
assert.equal(input.value, 'my untouched notes');
assert.equal(document.title, 'Inloggen · ScenarioDossier');
assert.equal(buttons[0]['aria-pressed'], 'true');
assert.equal(i18n.t('maatregelen'), 'maatregelen');
i18n.changeLanguage('en', en);
assert.equal(nodes[1].textContent, '0 of 8 spatial objects');
assert.equal(nodes[3].textContent, 'Inloggen');
assert.equal(nodes[6].textContent, '← Back to login');
assert.equal(input.value, 'my untouched notes');
assert.equal(i18n.t('maatregelen'), 'measures');
assert.equal(i18n.t('missing-key'), 'missing-key');
assert.equal(events, 2);
console.log('Language/form state, dynamic counts and fallback pass.');
