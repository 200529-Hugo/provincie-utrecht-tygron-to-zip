import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source = await readFile(new URL('../static/thumbnail-queue.js', import.meta.url), 'utf8');
const {ThumbnailQueue} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return {promise, resolve}; };
const within = (promise, ms = 1500) => new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(Error('Queue stalled')), ms);
    promise.then(value => { clearTimeout(timer); resolve(value); }, error => { clearTimeout(timer); reject(error); });
});

// Reproduce a 33-project catalog: project 0 is slow, the other 32 must complete.
const queue = new ThumbnailQueue(3);
const slow = deferred();
const allFast = deferred();
const order = [];
let active = 0;
let maximum = 0;
let fastCount = 0;
const results = Array.from({length: 33}, (_, index) => queue.enqueue(index, async () => {
    active++;
    maximum = Math.max(maximum, active);
    if (index === 0) await slow.promise;
    else await Promise.resolve();
    order.push(index);
    active--;
    if (index !== 0 && ++fastCount === 32) allFast.resolve();
    return index;
}));
await within(allFast.promise);
assert.equal(order.length, 32);
assert.equal(order.includes(0), false, 'A slow first image must not block later projects');
assert.equal(maximum, 3);
slow.resolve();
assert.deepEqual(await Promise.all(results), Array.from({length: 33}, (_, index) => index));

// Search/language rerendering must share an already-running request.
const single = new ThumbnailQueue(1);
const release = deferred();
let calls = 0;
const first = single.enqueue('city', async () => { calls++; await release.promise; return 'image'; });
const duplicate = single.enqueue('city', () => { throw Error('Duplicate request'); });
assert.equal(first, duplicate);
const cancelled = single.enqueue('old-search-result', () => { throw Error('Stale project was loaded'); });
const cancelledCheck = assert.rejects(cancelled, {name: 'AbortError'});
assert.equal(single.cancel('old-search-result'), true);
assert.equal(single.cancel('city'), false, 'Scrolling should not abandon a running Tygron session');
await cancelledCheck;
release.resolve();
assert.equal(await first, 'image');
assert.equal(calls, 1);

const closed = new ThumbnailQueue(1);
const started = deferred();
const activeResult = closed.enqueue('running', signal => new Promise((resolve, reject) => {
    signal.addEventListener('abort', () => reject(new DOMException('Cancelled', 'AbortError')), {once: true});
    started.resolve();
}));
const activeCheck = assert.rejects(activeResult, {name: 'AbortError'});
await started.promise;
closed.close();
await activeCheck;
await assert.rejects(closed.enqueue('new', () => 'unexpected'), {name: 'AbortError'});
console.log('33 projects: up to three parallel requests, no first-image blocking, deduplication and cancellation pass.');
