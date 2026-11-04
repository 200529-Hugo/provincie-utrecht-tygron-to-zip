import {request} from './client.js';

/**
 * @param {import('./models/map-assets.js').MapStyleRequest} payload
 * @returns {Promise<import('./models/map-assets.js').MapStyleResponse>}
 */
export function getMapStyle(payload, signal) {
    return request(payload.url, {signal, redirectOnUnauthorized: false});
}

/**
 * @param {import('./models/map-assets.js').TileMetadataRequest} payload
 * @returns {Promise<import('./models/map-assets.js').TileMetadataResponse>}
 */
export function getTileMetadata(payload, signal) {
    return request(payload.url, {signal, redirectOnUnauthorized: false});
}
