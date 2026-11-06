import {request} from './client.js';

/**
 * @param {import('./models/requests.js').ValidateArchiveRequest} payload
 * @returns {Promise<import('./models/responses.js').ValidateArchiveResponse>}
 */
export function validateDossierArchive(payload) {
    return request('/api/validate', {method: 'POST', body: payload, requestType: 'zip'});
}

/**
 * @param {import('./models/requests.js').DownloadRequest} payload
 * @returns {Promise<import('./models/responses.js').DownloadResponse>}
 */
export function downloadArchive(payload) {
    return request(`/api/download/${encodeURIComponent(payload.name)}`, {responseType: 'binary'});
}
