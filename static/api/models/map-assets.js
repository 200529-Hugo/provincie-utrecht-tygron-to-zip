/**
 * De kaartserver is een externe bron met eigen uitbreidbare JSON-documenten.
 * Alleen de velden die de kaartpreview gebruikt worden hier beschreven.
 * @typedef {{url: string}} MapStyleRequest
 * @typedef {{version?: number, sources: Object<string, {type?: string, url?: string}>}} MapStyleResponse
 * @typedef {{url: string}} TileMetadataRequest
 * @typedef {{bounds?: Array<number>, tiles?: Array<string>}} TileMetadataResponse
 */
export {};
