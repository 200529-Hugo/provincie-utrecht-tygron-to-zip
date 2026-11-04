// Gegenereerd vanuit Python-modellen, pas de bronmodellen aan.
// Opnieuw opbouwen met scripts/generate_api_models.py

/**
 * @typedef {Object} ArchiveSummaryResponse
 * @property {string} schema
 * @property {string} project
 * @property {string} scenario
 * @property {string} exported_at
 * @property {string} source
 * @property {string} crs
 * @property {ComponentCountsResponse} components
 * @property {string} notes
 * @property {RecordMetadataResponse} record
 * @property {DecisionMetadataResponse} decision
 * @property {string} software
 * @property {boolean} token_archived
 * @property {Array<string>} warnings
 * @property {string} validation
 * @property {number} size
 */

/**
 * @typedef {Object} ComponentCountsResponse
 * @property {number} overlays
 * @property {number} indicators
 * @property {number} measures
 * @property {number} alerts
 */

/**
 * @typedef {Object} DecisionMetadataResponse
 * @property {string} date
 * @property {string} status
 * @property {string} selected_scenario
 * @property {string} alternatives
 * @property {string} rationale
 */

/**
 * @typedef {Object} DemoCatalogResponse
 * @property {Array<DemoProjectResponse>} projects
 */

/**
 * @typedef {Object} DemoProjectResponse
 * @property {string} id
 * @property {string} name
 * @property {Array<DemoScenarioResponse>} scenarios
 */

/**
 * @typedef {Array<DemoProjectResponse>} DemoProjectsResponse
 */

/**
 * @typedef {Object} DemoScenarioResponse
 * @property {string} id
 * @property {string} name
 * @property {string} description
 */

/**
 * @typedef {Array<DemoScenarioResponse>} DemoScenariosResponse
 */

/**
 * @typedef {(Blob|null)} DemoThumbnailResponse
 */

/**
 * @typedef {Blob} DownloadResponse
 */

/**
 * @typedef {Object} ErrorResponse
 * @property {string} error
 */

/**
 * @typedef {Object} ExportResponse
 * @property {string} filename
 * @property {string} download
 * @property {ArchiveSummaryResponse} summary
 * @property {boolean} ok
 */

/**
 * @typedef {Object} InspectResponse
 * @property {string} project
 * @property {string} scenario
 * @property {ComponentCountsResponse} counts
 * @property {number} spatial
 * @property {Array<string>} warnings
 * @property {Array<PreviewFeatureResponse>} preview
 * @property {Array<ScenarioItemResponse>} items
 */

/**
 * @typedef {Object} LoginResponse
 * @property {boolean} ok
 */

/**
 * @typedef {Object} LogoutResponse
 * @property {boolean} ok
 */

/**
 * @typedef {string} ManualResponse
 */

/**
 * @typedef {Object} MapConfigResponse
 * @property {string} style_url
 */

/**
 * @typedef {Object} PreviewFeatureResponse
 * @property {string} component
 * @property {string} key
 * @property {Object<string, *>} feature
 */

/**
 * @typedef {Object} ProjectResponse
 * @property {string} file_name
 * @property {string} name
 * @property {number} active_version
 * @property {Array<string>} versions
 * @property {string} description
 * @property {string} domain
 * @property {string} revision
 */

/**
 * @typedef {(Blob|null)} ProjectThumbnailResponse
 */

/**
 * @typedef {Object} ProjectsResponse
 * @property {Array<ProjectResponse>} projects
 */

/**
 * @typedef {Object} RecordMetadataResponse
 * @property {string} reference
 * @property {string} owner
 * @property {string} author
 * @property {string} classification
 * @property {string} retention_period
 */

/**
 * @typedef {Object} ScenarioItemResponse
 * @property {string} key
 * @property {string} component
 * @property {string} name
 * @property {string} detail
 * @property {boolean} spatial
 * @property {string} geometry_type
 */

/**
 * @typedef {Object} SessionStatusResponse
 * @property {boolean} authenticated
 */

/**
 * @typedef {Object<string, string>} TranslationsResponse
 */

/**
 * @typedef {Object} ValidateArchiveResponse
 * @property {string} schema
 * @property {string} validated_at
 * @property {string} status
 * @property {number} checks_ok
 * @property {number} checks_failed
 * @property {Array<ValidationCheckResponse>} checks
 * @property {string} filename
 * @property {number} archive_size
 * @property {string} project
 * @property {string} scenario
 * @property {string} exported_at
 * @property {Object<string, number>} components
 */

/**
 * @typedef {Object} ValidationCheckResponse
 * @property {string} check
 * @property {string} status
 * @property {string} detail
 */

export {};
