import {jsonRequest, request} from './client.js';

/**
 * @param {import('./models/requests.js').MapConfigRequest} payload
 * @returns {Promise<import('./models/responses.js').MapConfigResponse>}
 */
export function getMapConfig(payload = {}) {
    return jsonRequest('/api/map-config');
}

/**
 * @param {import('./models/requests.js').ManualRequest} payload
 * @returns {Promise<import('./models/responses.js').ManualResponse>}
 */
export function getManual(payload = {}) {
    return request('/api/werkinstructie', {responseType: 'text'});
}

/**
 * @param {import('./models/requests.js').TranslationsRequest} payload
 * @returns {Promise<import('./models/responses.js').TranslationsResponse>}
 */
export function getTranslations(payload) {
    return jsonRequest(`/api/translations/${encodeURIComponent(payload.language)}`);
}
