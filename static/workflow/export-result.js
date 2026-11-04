import {t} from '../i18n.js';

const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;', "'":'&#39;'}[c]));
const $ = selector => document.querySelector(selector);

// Het succesvenster toont het resultaat en verstuurt zelf geen API-verzoeken.
export function renderExportResult(data) {
    $('#doneText').textContent =
        `${data.summary.project} · ${data.summary.scenario} ` +
        t('is gereed voor overdracht en archivering.');
    const validationRow = data.summary.validation
        ? `
            <span>${t('Automatische validatie')}</span>
            <b>${escapeHtml(t(data.summary.validation))}</b>
        `
        : '';

    $('#package').innerHTML = `
        <b>${escapeHtml(data.filename)}</b>
        <span>${(data.summary.size / 1024).toFixed(1)} KB</span>
        <span>${t('Bestandsformaat')}</span>
        <b>${t('ZIP + GeoPackage + HTML-rapport')}</b>
        <span>${t('Integriteitscontrole')}</span>
        <b>SHA-256</b>
        ${validationRow}
    `;
    $('#download').href = data.download;

}
