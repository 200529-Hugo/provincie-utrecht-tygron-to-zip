import {t} from '../i18n.js';

/**
 * Alleen dit bestand verstuurt HTTP-verzoeken vanuit de browser.
 * De modules per onderwerp kennen de URL en hun payload- en antwoordmodel.
 */
export async function request(url, {
    method = 'GET', body, requestType = 'json', responseType = 'json',
    signal, redirectOnUnauthorized = true, optionalImage = false
} = {}) {
    let response;
    const options = {method, signal, cache: 'no-store'};
    if (body !== undefined) {
        options.headers = {'Content-Type': requestType === 'json' ? 'application/json' : 'application/zip'};
        options.body = requestType === 'json' ? JSON.stringify(body) : body;
    }
    try {
        response = await fetch(url, options);
    } catch (error) {
        if (error.name === 'AbortError' || signal?.aborted) throw error;
        throw Error(t('De server is niet bereikbaar. Probeer opnieuw.'));
    }
    if (response.status === 401 && redirectOnUnauthorized && !url.endsWith('/auth/login')) {
        location.assign('/login');
    }
    if (optionalImage && (!response.ok || response.status === 204)) return null;
    if (!response.ok) {
        /** @type {Partial<import('./models/responses.js').ErrorResponse>} */
        const failure = await response.json().catch(() => ({}));
        throw Error(failure.error || t('Het verzoek kon niet worden verwerkt.'));
    }
    if (responseType === 'text') return response.text();
    if (responseType === 'image') {
        if (!/^image\/(png|svg\+xml)(;|$)/.test(response.headers.get('Content-Type') || '')) return null;
        return response.blob();
    }
    if (responseType === 'binary') return response.blob();
    try {
        return await response.json();
    } catch {
        throw Error(t('Het verzoek kon niet worden verwerkt.'));
    }
}

export function jsonRequest(url, payload, options = {}) {
    return request(url, {method: payload === undefined ? 'GET' : 'POST', body: payload, ...options});
}
