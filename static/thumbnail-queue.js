// Laad een begrensd aantal previews tegelijk en elk project maximaal eenmaal.
export class ThumbnailQueue {
    constructor(concurrency = 3) {
        this.concurrency = Math.max(1, Math.min(6, Math.floor(Number(concurrency) || 3)));
        this.pending = new Map();
        this.waiting = [];
        this.active = 0;
        this.closed = false;
    }

    enqueue(key, task) {
        if (this.closed) return Promise.reject(new DOMException('Cancelled', 'AbortError'));
        if (this.pending.has(key)) return this.pending.get(key).promise;
        const job = {key, task, started: false, controller: new AbortController()};
        job.promise = new Promise((resolve, reject) => { job.resolve = resolve; job.reject = reject; });
        this.pending.set(key, job);
        this.waiting.push(job);
        this.drain();
        return job.promise;
    }

    drain() {
        while (!this.closed && this.active < this.concurrency && this.waiting.length) {
            const job = this.waiting.shift();
            job.started = true;
            this.active++;
            Promise.resolve().then(() => job.task(job.controller.signal))
                .then(job.resolve, job.reject)
                .finally(() => {
                    this.active--;
                    this.pending.delete(job.key);
                    this.drain();
                });
        }
    }

    cancel(key) {
        const job = this.pending.get(key);
        if (!job || job.started) return false;
        this.waiting = this.waiting.filter(item => item !== job);
        this.pending.delete(key);
        job.controller.abort();
        job.reject(new DOMException('Cancelled', 'AbortError'));
        return true;
    }

    clearQueued() {
        [...this.waiting].forEach(job => this.cancel(job.key));
    }

    close() {
        this.closed = true;
        this.clearQueued();
        this.pending.forEach(job => job.controller.abort());
    }
}
