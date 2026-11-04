import {jsonRequest, request} from './client.js';

/**
 * @param {import('./models/requests.js').AccountProjectsRequest} payload
 * @returns {Promise<import('./models/responses.js').ProjectsResponse>}
 */
export function getAccountProjects(payload = {}) {
    return jsonRequest('/api/tygron/projects');
}

/**
 * @param {import('./models/requests.js').LegacyProjectsRequest} payload
 * @returns {Promise<import('./models/responses.js').ProjectsResponse>}
 */
export function getLegacyProjects(payload) {
    return jsonRequest('/api/tygron/projects', payload);
}

/**
 * @param {import('./models/requests.js').DemoCatalogRequest} payload
 * @returns {Promise<import('./models/responses.js').DemoCatalogResponse>}
 */
export function getDemoCatalog(payload = {}) {
    return jsonRequest('/api/demo');
}

/**
 * @param {import('./models/requests.js').DemoProjectsRequest} payload
 * @returns {Promise<import('./models/responses.js').DemoProjectsResponse>}
 */
export function getDemoProjects(payload = {}) {
    return jsonRequest('/api/demo/projects');
}

/**
 * @param {import('./models/requests.js').DemoScenariosRequest} payload
 * @returns {Promise<import('./models/responses.js').DemoScenariosResponse>}
 */
export function getDemoScenarios(payload) {
    return jsonRequest(`/api/demo/scenarios/${encodeURIComponent(payload.project_id)}`);
}

/**
 * @param {import('./models/requests.js').ProjectThumbnailRequest} payload
 * @returns {Promise<import('./models/responses.js').ProjectThumbnailResponse>}
 */
export function getProjectThumbnail(payload, signal) {
    return request('/api/tygron/thumbnail', {
        method: 'POST', body: payload, signal, responseType: 'image', optionalImage: true
    });
}

/**
 * @param {import('./models/requests.js').DemoThumbnailRequest} payload
 * @returns {Promise<import('./models/responses.js').DemoThumbnailResponse>}
 */
export function getDemoThumbnail(payload, signal) {
    return request(`/api/demo/thumbnail/${encodeURIComponent(payload.project_id)}`, {
        signal, responseType: 'image', optionalImage: true
    });
}
