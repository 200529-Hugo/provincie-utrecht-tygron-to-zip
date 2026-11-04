// Gegenereerd vanuit Python-modellen, pas de bronmodellen aan.
// Opnieuw opbouwen met scripts/generate_api_models.py

/**
 * @typedef {Object} AccountProjectsRequest
 */

/**
 * @typedef {Object} DemoCatalogRequest
 */

/**
 * @typedef {Object} DemoProjectsRequest
 */

/**
 * @typedef {Object} DemoScenariosRequest
 * @property {string} project_id
 */

/**
 * @typedef {Object} DemoThumbnailRequest
 * @property {string} project_id
 */

/**
 * @typedef {Object} DossierDetails
 * @property {string} [reference]
 * @property {string} [owner]
 * @property {string} [author]
 * @property {string} [decision_date]
 * @property {string} [decision_status]
 * @property {string} [alternatives]
 * @property {string} [classification]
 * @property {string} [retention_period]
 */

/**
 * @typedef {Object} DownloadRequest
 * @property {string} name
 */

/**
 * @typedef {Object} ExportRequest
 * @property {string} [source]
 * @property {string} [project_id]
 * @property {string} [scenario_id]
 * @property {string} [base_url]
 * @property {string} [token] Vertrouwelijk, niet loggen.
 * @property {string} [username]
 * @property {string} [login_key] Vertrouwelijk, niet loggen.
 * @property {string} [domain]
 * @property {string} [project_file]
 * @property {string} [project_name]
 * @property {string} [scenario_name]
 * @property {boolean} [authenticated]
 * @property {string} [notes]
 * @property {DossierDetails} [dossier]
 * @property {(Array<string>|null)} [components]
 * @property {(Object<string, Array<string>>|null)} [selected_items]
 * @property {boolean} [rasters]
 */

/**
 * @typedef {Object} InspectRequest
 * @property {string} [source]
 * @property {string} [project_id]
 * @property {string} [scenario_id]
 * @property {string} [base_url]
 * @property {string} [token] Vertrouwelijk, niet loggen.
 * @property {string} [username]
 * @property {string} [login_key] Vertrouwelijk, niet loggen.
 * @property {string} [domain]
 * @property {string} [project_file]
 * @property {string} [project_name]
 * @property {string} [scenario_name]
 * @property {boolean} [authenticated]
 */

/**
 * @typedef {Object} LegacyProjectsRequest
 * @property {string} base_url
 * @property {string} username
 * @property {string} login_key Vertrouwelijk, niet loggen.
 * @property {string} [domain]
 */

/**
 * @typedef {Object} LoginRequest
 * @property {string} username
 * @property {string} password Vertrouwelijk, niet loggen.
 * @property {string} [base_url]
 * @property {string} [domain]
 */

/**
 * @typedef {Object} LogoutRequest
 */

/**
 * @typedef {Object} ManualRequest
 */

/**
 * @typedef {Object} MapConfigRequest
 */

/**
 * @typedef {Object} ProjectThumbnailRequest
 * @property {string} project_file
 */

/**
 * @typedef {Object} SessionStatusRequest
 */

/**
 * @typedef {Object} TranslationsRequest
 * @property {string} language
 */

/**
 * @typedef {Blob} ValidateArchiveRequest
 */

export {};
