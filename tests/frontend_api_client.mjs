import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source = (await readFile(new URL('../static/api/client.js', import.meta.url), 'utf8'))
    .replace("import {t} from '../i18n.js';", 'const t = message => message;');
const {request, jsonRequest} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const calls = [];
const redirects = [];
globalThis.location = {assign: url => redirects.push(url)};
let nextResponse = {ok: true, status: 200, json: async () => ({ok: true})};
globalThis.fetch = async (url, options) => { calls.push({url, options}); return nextResponse; };

assert.deepEqual(await jsonRequest('/api/auth/login', {username: 'u', password: 'p'}), {ok: true});
assert.equal(calls[0].options.method, 'POST');
assert.equal(calls[0].options.headers['Content-Type'], 'application/json');
assert.deepEqual(JSON.parse(calls[0].options.body), {username: 'u', password: 'p'});
await jsonRequest('/api/demo/projects');
assert.equal(calls.at(-1).options.method, 'GET');
assert.equal(calls.at(-1).options.body, undefined);

nextResponse = {ok: false, status: 401, json: async () => ({error: 'Invalid session token'})};
await assert.rejects(jsonRequest('/api/inspect', {}, {redirectOnUnauthorized: false}), /Invalid session token/);
assert.deepEqual(redirects, []);
await assert.rejects(jsonRequest('/api/inspect', {}), /Invalid session token/);
assert.deepEqual(redirects, ['/login']);
await assert.rejects(jsonRequest('/api/auth/login', {}), /Invalid session token/);
assert.equal(redirects.length, 1);

nextResponse = {ok: true, status: 204};
assert.equal(await request('/image', {responseType: 'image', optionalImage: true}), null);
nextResponse = {ok: false, status: 502};
assert.equal(await request('/image', {responseType: 'image', optionalImage: true}), null);
const image = new Blob(['image'], {type: 'image/png'});
nextResponse = {ok: true, status: 200, headers: new Headers({'Content-Type': 'image/png'}), blob: async () => image};
assert.equal(await request('/image', {responseType: 'image'}), image);
nextResponse.headers = new Headers({'Content-Type': 'text/html'});
assert.equal(await request('/image', {responseType: 'image'}), null);

const upload = new Blob(['ZIP'], {type: 'application/zip'});
nextResponse = {ok: true, status: 200, json: async () => ({status: 'goedgekeurd'})};
await request('/api/validate', {method: 'POST', body: upload, requestType: 'zip'});
assert.equal(calls.at(-1).options.body, upload);
assert.equal(calls.at(-1).options.headers['Content-Type'], 'application/zip');
nextResponse = {ok: true, text: async () => '# Handleiding'};
assert.equal(await request('/api/werkinstructie', {responseType: 'text'}), '# Handleiding');

nextResponse = {ok: true, json: async () => { throw new SyntaxError(); }};
await assert.rejects(jsonRequest('/broken'), /Het verzoek kon niet worden verwerkt/);
globalThis.fetch = async () => { throw new DOMException('Cancelled', 'AbortError'); };
await assert.rejects(request('/cancelled'), {name: 'AbortError'});
console.log('JSON, images, ZIP uploads, text, errors and scoped authentication redirects pass.');
