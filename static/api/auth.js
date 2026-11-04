import {jsonRequest} from './client.js';

/**
 * @param {import('./models/requests.js').LoginRequest} payload
 * @returns {Promise<import('./models/responses.js').LoginResponse>}
 */
export function loginAccount(payload) {
    return jsonRequest('/api/auth/login', payload);
}

/**
 * @param {import('./models/requests.js').LogoutRequest} payload
 * @returns {Promise<import('./models/responses.js').LogoutResponse>}
 */
export function logoutAccount(payload = {}) {
    return jsonRequest('/api/auth/logout', payload);
}

/**
 * @param {import('./models/requests.js').SessionStatusRequest} payload
 * @returns {Promise<import('./models/responses.js').SessionStatusResponse>}
 */
export function getSessionStatus(payload = {}) {
    return jsonRequest('/api/auth/session');
}
