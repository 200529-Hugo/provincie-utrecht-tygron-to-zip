import {jsonRequest} from './client.js';

/**
 * @param {import('./models/requests.js').InspectRequest} payload
 * @returns {Promise<import('./models/responses.js').InspectResponse>}
 */
export function inspectScenario(payload, options = {}) {
    return jsonRequest('/api/inspect', payload, options);
}

/**
 * @param {import('./models/requests.js').ExportRequest} payload
 * @returns {Promise<import('./models/responses.js').ExportResponse>}
 */
export function exportDossier(payload, options = {}) {
    return jsonRequest('/api/export', payload, options);
}
