import {t} from './i18n.js';
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
const mode = parameters.get('mode');
const activeSessionMode = mode === 'tygron';
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
        $('#export').disabled = exporting || !inspected || count === 0;
    },
    onShowOnMap: async key => {
        reviewMap.open = true;
        await ensureScenarioMap();
        focusScenarioItem(key);
        if (window.matchMedia('(max-width: 1000px)').matches) reviewMap.scrollIntoView({behavior: 'smooth', block: 'start'});
    }
});
const updateItemSelection = () => selectionPanel.refresh();
const sourceForm = createSourceForm({mode, parameters, onScenarioChanged: inspect, onError: toast});

function setReviewTab(name, scroll = false) {
    reviewTab = name;
    $$('[data-review-tab]').forEach(button => {
        const active = button.dataset.reviewTab === name;
        button.setAttribute('aria-selected', String(active));
        button.tabIndex = active ? 0 : -1;
    });
    $('#selectionPanel').hidden = name !== 'selection';
    $('#detailsPanel').hidden = name !== 'details';
    $('#reviewNext').textContent = t(name === 'selection' ? 'Verder: dossiergegevens' : 'Terug naar selectie');
    if (scroll) $('.review-tabs').scrollIntoView({behavior: 'smooth', block: 'start'});
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
    const button = $('#inspect');
    const sessionForm = $('#activeSessionForm');

    sessionForm?.setAttribute('aria-busy', 'true');
    if (sessionForm) $('#sessionConnectionStatus').textContent = '';
    button.disabled = true;
    button.textContent = t('Controleren…');
    $('#reviewScenario').disabled = true;
    inspected = undefined;
    hasExport = false;
    $('#export').disabled = true;
    $('#step3').setAttribute('aria-busy', 'true');
    $('#inspectionStatus').textContent = t('Scenario laden…');
    $('#retryInspect').classList.add('hidden');

    try {
        inspected = await inspectScenario(sourceForm.payload(), {redirectOnUnauthorized: !activeSessionMode});
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
        if (sessionForm) $('#sessionConnectionStatus').textContent = error.message;
        $('#inspectionStatus').textContent = error.message;
        $('#retryInspect').classList.remove('hidden');
        toast(error.message);
    } finally {
        sessionForm?.setAttribute('aria-busy', 'false');
        $('#step3').setAttribute('aria-busy', 'false');
        $('#reviewScenario').disabled = false;
        button.disabled = false;
        button.innerHTML = t('Verbinding controleren');
    }
}

async function doExport() {
    const button = $('#export');

    button.disabled = true;
    button.textContent = t('Dossier opbouwen…');
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
        const data = await exportDossier(exportPayload, {redirectOnUnauthorized: !activeSessionMode});

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
        button.innerHTML = t('Dossier maken');
    }
}

async function init() {
    $('#decisionDate').value = new Intl.DateTimeFormat('sv-SE').format(new Date());
    // De sessiepagina heeft geen projectlijst of demonstratiegegevens nodig.
    if (activeSessionMode) return;
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

const activeSessionForm = $('#activeSessionForm');
if (activeSessionForm) {
    activeSessionForm.onsubmit = event => { event.preventDefault(); inspect(); };
    activeSessionForm.addEventListener('input', () => {
        $('#sessionConnectionStatus').textContent = '';
        // Controleer gewijzigde sessiegegevens opnieuw voordat export mogelijk is.
        inspected = undefined;
        hasExport = false;
        $('#export').disabled = true;
        $$('.workflow-steps button').filter(button => Number(button.dataset.step) > 2)
            .forEach(button => { button.disabled = true; });
    });
} else $('#inspect').onclick = inspect;
$('#export').onclick = doExport;
$('#reviewNext').onclick = () => setReviewTab(reviewTab === 'selection' ? 'details' : 'selection', true);
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
