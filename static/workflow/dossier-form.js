const $ = selector => document.querySelector(selector);

// Dit bestand koppelt de dossiergegevens in het formulier aan het API-model.
/** @returns {import('../api/models/requests.js').DossierDetails} */
export function readDossierFields() {
    return {
        reference: $('#recordReference').value.trim(),
        owner: $('#recordOwner').value.trim(),
        author: $('#recordAuthor').value.trim(),
        decision_date: $('#decisionDate').value,
        decision_status: $('#decisionStatus').value,
        alternatives: $('#alternatives').value.trim(),
        classification: $('#classification').value,
        retention_period: $('#retentionPeriod').value.trim()
    };
}

function defaultReference(project, scenario) {
    const normalized = `${project}-${scenario}`
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-zA-Z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        .toUpperCase();

    return normalized.slice(0, 42);
}

export function setDefaultReference(project, scenario) {
    if (!$('#recordReference').value.trim()) $('#recordReference').value = defaultReference(project, scenario);
}
