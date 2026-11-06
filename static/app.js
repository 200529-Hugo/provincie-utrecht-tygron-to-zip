import {t} from './i18n.js';
import {bindSecretToggles} from './secret-toggle.js';
import {createSourceForm} from './workflow/source-form.js';
import {inspectScenario, exportDossier} from './api/workflow.js';
import {createSelectionPanel} from './workflow/selection-panel.js';
import {renderExportResult} from './workflow/export-result.js';
import {readDossierFields, setDefaultReference} from './workflow/dossier-form.js';
import {
    drawScenarioMap,
    focusScenarioItem,
    setScenarioSelection,
    resizeScenarioMap
} from './scenario-map.js';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];

const parameters = new URLSearchParams(location.search);
const mode = $('#content').dataset.workflowMode;
const connectionForm = $('#step2 form');
const connectionButton = $('#inspect');
const connectionStatus = $('#sessionConnectionStatus');
const reviewNext = $('#reviewNext');
const exportButton = $('#export');
const accountMode = mode === 'account';
const demoSelection = mode === 'demo' && parameters.has('project_id');
const overviewSelection = accountMode || demoSelection;
let inspected;
let hasExport = false;

let reviewTab = 'selection';
let exporting = false;
let mappedInspection;
let mapTask = Promise.resolve();
const reviewMap = $('#reviewMap');
if (window.matchMedia('(max-width: 1000px)').matches) reviewMap.open = false;

const selectionPanel = createSelectionPanel({
    onChange: (count, keys) => {
        setScenarioSelection(keys);
        exportButton.disabled = exporting || !inspected || count === 0;
    },
    onShowOnMap: async key => {
        reviewMap.open = true;
        await ensureScenarioMap();
        focusScenarioItem(key);
        if (window.matchMedia('(max-width: 1000px)').matches) reviewMap.scrollIntoView({behavior: 'smooth', block: 'start'});
    }
});
const updateItemSelection = () => selectionPanel.refresh();
const sourceForm = createSourceForm({mode, parameters, onScenarioChanged: inspect, onConnectionChanged: invalidateConnection});

function setReviewTab(name, scroll = false) {
    reviewTab = name;
    $$('[data-review-tab]').forEach(button => {
        const active = button.dataset.reviewTab === name;
        button.setAttribute('aria-selected', String(active));
        button.tabIndex = active ? 0 : -1;
    });
    $('#selectionPanel').hidden = name !== 'selection';
    $('#detailsPanel').hidden = name !== 'details';
    reviewNext.firstElementChild.textContent = t(name === 'selection' ? 'Naar dossiergegevens' : 'Terug naar selectie');
    reviewNext.lastElementChild.classList.toggle('chevron--left', name === 'details');
    if (scroll) {
        const tab = $(`[data-review-tab="${name}"]`);
        tab.focus({preventScroll: true});
        tab.scrollIntoView({block: 'start'});
    }
}

async function ensureScenarioMap() {
    if (!inspected || !reviewMap.open) return;
    if (mappedInspection !== inspected) {
        const current = inspected;
        mappedInspection = current;
        mapTask = drawScenarioMap(current.preview).then(updateItemSelection).catch(error => {
            mappedInspection = undefined;
            $('#basemapStatus').textContent = t('De kaart kon niet worden geladen. Je kunt je selectie wel exporteren.');
            toast(error.message);
        });
    }
    await mapTask;
    requestAnimationFrame(resizeScenarioMap);
}

function toast(message) {
    const element = $('#toast');

    element.textContent = message;
    element.classList.add('show');
    setTimeout(() => element.classList.remove('show'), 4200);
}

function step(number) {
    $$('.panel').forEach(panel => panel.classList.remove('active'));
    $('#step' + number).classList.add('active');
    $$('.steps button').forEach(button => {
        const target = Number(button.dataset.step);
        button.classList.toggle('active', target === number);
        button.classList.toggle('completed', target < number);
        if (target === number) button.setAttribute('aria-current', 'step');
        else button.removeAttribute('aria-current');
        if (target === 3) button.disabled = !inspected && number !== 3;
        if (target === 4) button.disabled = !hasExport;
    });
    scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

async function inspect() {
    if (connectionForm?.getAttribute('aria-busy') === 'true') return;
    if (connectionForm) {
        invalidateConnection();
        connectionForm.setAttribute('aria-busy', 'true');
        connectionForm.inert = true;
        connectionButton.disabled = true;
        connectionButton.textContent = t('Controleren…');
    }
    $('#reviewScenario').disabled = true;
    inspected = undefined;
    hasExport = false;
    exportButton.disabled = true;
    $('#step3').setAttribute('aria-busy', 'true');
    $('#inspectionStatus').textContent = t('Scenario laden…');
    $('#retryInspect').classList.add('hidden');

    try {
        inspected = await inspectScenario(sourceForm.payload(), {redirectOnUnauthorized: accountMode});
        $('#inspectionStatus').textContent = '';
        $('#selectionTitle').textContent = `${inspected.project} · ${inspected.scenario}`;
        setDefaultReference(inspected.project, inspected.scenario);
        selectionPanel.renderCategories(inspected.counts);
        $('#spatialCount').textContent = t('{count} ruimtelijke objecten', {count: inspected.spatial});
        selectionPanel.renderItems(inspected.items || []);

        if (inspected.warnings.length) {
            toast(inspected.warnings.join(' '));
        }

        step(3);
        await ensureScenarioMap();
        updateItemSelection();
    } catch (error) {
        if (connectionForm) connectionStatus.textContent = error.message;
        $('#inspectionStatus').textContent = error.message;
        $('#retryInspect').classList.remove('hidden');
        toast(error.message);
    } finally {
        $('#step3').setAttribute('aria-busy', 'false');
        $('#reviewScenario').disabled = false;
        if (connectionForm) {
            connectionForm.inert = false;
            connectionForm.setAttribute('aria-busy', 'false');
            connectionButton.disabled = $('#liveProject')?.disabled ?? false;
            connectionButton.textContent = t('Verbinding controleren');
        }
    }
}

async function doExport() {
    exportButton.disabled = true;
    exportButton.firstElementChild.textContent = t('Dossier opbouwen…');
    exporting = true;

    try {
        const exportPayload = {
            ...sourceForm.payload(),
            notes: $('#notes').value,
            dossier: readDossierFields(),
            components: selectionPanel.selectedComponents(),
            selected_items: selectionPanel.selectedItems(),
            rasters: true
        };
        const data = await exportDossier(exportPayload, {redirectOnUnauthorized: accountMode});

        renderExportResult(data);

        if (data.summary.warnings.length) {
            toast(data.summary.warnings.join(' '));
        }

        hasExport = true;
        step(4);
    } catch (error) {
        toast(error.message);
    } finally {
        exporting = false;
        updateItemSelection();
        exportButton.firstElementChild.textContent = t('Dossier maken');
    }
}

async function init() {
    $('#decisionDate').value = new Intl.DateTimeFormat('sv-SE').format(new Date());
    if (connectionForm) return;
    if (overviewSelection) step(3);
    try {
        if (await sourceForm.initialize()) await inspect();
    } catch (error) {
        toast(error.message);
        if (overviewSelection) {
            $('#inspectionStatus').textContent = error.message;
            $('#retryInspect').classList.remove('hidden');
        }
    }
}

function invalidateConnection() {
    connectionStatus.textContent = '';
    // Controleer gewijzigde brongegevens opnieuw voordat export mogelijk is.
    inspected = undefined;
    hasExport = false;
    exportButton.disabled = true;
    $$('.workflow-steps button').filter(button => Number(button.dataset.step) > 2)
        .forEach(button => { button.disabled = true; });
}

bindSecretToggles();
if (connectionForm) {
    connectionForm.onsubmit = event => {
        event.preventDefault();
        if (!connectionButton.disabled) inspect();
    };
    connectionForm.addEventListener('input', invalidateConnection);
}
exportButton.onclick = doExport;
reviewNext.onclick = () => setReviewTab(reviewTab === 'selection' ? 'details' : 'selection', true);
$$('[data-review-tab]').forEach(button => {
    button.onclick = () => setReviewTab(button.dataset.reviewTab);
    button.onkeydown = event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const name = event.key === 'Home' ? 'selection' : event.key === 'End' ? 'details' : reviewTab === 'selection' ? 'details' : 'selection';
        setReviewTab(name);
        $(`[data-review-tab="${name}"]`).focus();
    };
});
reviewMap.addEventListener('toggle', ensureScenarioMap);
function chooseProject() {
    if (accountMode) location.assign('/projecten');
    else if (demoSelection) location.assign('/projecten?mode=demo');
    else step(2);
}
$$('.back').forEach(button => { button.onclick = chooseProject; });
$('#again').onclick = chooseProject;
$('#retryInspect').onclick = () => overviewSelection && !inspected ? init() : inspect();
$$('.workflow-steps button').forEach(button => {
    if (Number(button.dataset.step) < 2) return;
    button.onclick = event => {
        event.preventDefault();
        if (button.disabled) return;
        if (Number(button.dataset.step) === 2) chooseProject();
        else step(Number(button.dataset.step));
    };
});

init();

document.addEventListener('languagechange', () => {
    setReviewTab(reviewTab);
    if (inspected) {
        selectionPanel.renderCategories(inspected.counts);
        updateItemSelection();
        $('#doneText').textContent = `${inspected.project} · ${inspected.scenario} ${t('is gereed voor overdracht en archivering.')}`;
    }

});
