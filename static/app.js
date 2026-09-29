import {
    drawScenarioMap,
    focusScenarioItem,
    setScenarioSelection
} from './scenario-map.js';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];

let source = 'demo';
let demo;
let inspected;
let liveProjects = [];

const labels = {
    overlays: 'overlays',
    indicators: 'indicatoren',
    measures: 'maatregelen',
    alerts: 'alerts'
};
const componentOrder = ['overlays', 'indicators', 'measures', 'alerts'];

function itemCheckboxes() {
    return $$('#itemGroups input[data-item-key]');
}

function selectedItems() {
    const selection = Object.fromEntries(componentOrder.map(name => [name, []]));
    itemCheckboxes().filter(input => input.checked).forEach(input => {
        selection[input.dataset.component].push(input.dataset.itemKey);
    });
    return selection;
}

function updateItemSelection() {
    const inputs = itemCheckboxes();
    const checked = inputs.filter(input => input.checked);
    const spatial = inputs.filter(input => input.dataset.spatial === 'true');
    const selectedSpatial = checked.filter(input => input.dataset.spatial === 'true');

    componentOrder.forEach(component => {
        const group = $(`#itemGroups input[data-group="${component}"]`);
        if (!group) {
            return;
        }
        const children = inputs.filter(input => input.dataset.component === component);
        const selected = children.filter(input => input.checked).length;
        group.checked = selected === children.length && children.length > 0;
        group.indeterminate = selected > 0 && selected < children.length;
        const count = $(`#itemGroups [data-group-count="${component}"]`);
        count.textContent = `${selected}/${children.length}`;
    });

    $('#selectionCount').textContent = `${checked.length} van ${inputs.length} geselecteerd`;
    $('#spatialCount').textContent = `${selectedSpatial.length} van ${spatial.length} ruimtelijke objecten`;
    $('#export').disabled = checked.length === 0;
    setScenarioSelection(new Set(checked.map(input => input.dataset.itemKey)));
}

function filterItems() {
    const query = $('#itemSearch').value.trim().toLocaleLowerCase('nl');
    $$('.item-group').forEach(group => {
        let visible = 0;
        group.querySelectorAll('.item-row').forEach(row => {
            const matches = !query || row.dataset.search.includes(query);
            row.hidden = !matches;
            visible += Number(matches);
        });
        group.hidden = visible === 0;
    });
}

function renderItemSelector(items) {
    const container = $('#itemGroups');
    container.replaceChildren();

    componentOrder.forEach(component => {
        const componentItems = items.filter(item => item.component === component);
        if (!componentItems.length) {
            return;
        }

        const group = document.createElement('section');
        group.className = 'item-group';

        const heading = document.createElement('label');
        heading.className = 'item-group-head';
        const groupCheck = document.createElement('input');
        groupCheck.type = 'checkbox';
        groupCheck.checked = true;
        groupCheck.dataset.group = component;
        const title = document.createElement('strong');
        title.textContent = labels[component];
        const count = document.createElement('small');
        count.dataset.groupCount = component;
        heading.append(groupCheck, title, count);
        group.append(heading);

        const list = document.createElement('div');
        list.className = 'item-list';
        componentItems.forEach(item => {
            const row = document.createElement('div');
            row.className = 'item-row';
            row.dataset.search = `${item.name} ${item.detail} ${labels[component]}`
                .toLocaleLowerCase('nl');

            const toggle = document.createElement('label');
            toggle.className = 'item-toggle';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = true;
            checkbox.dataset.itemKey = item.key;
            checkbox.dataset.component = component;
            checkbox.dataset.spatial = String(item.spatial);
            checkbox.setAttribute('aria-label', `${item.name} opnemen in het dossier`);
            toggle.append(checkbox);

            const copy = document.createElement('span');
            copy.className = 'item-copy';
            const name = document.createElement('strong');
            name.textContent = item.name;
            const detail = document.createElement('small');
            detail.textContent = item.detail || (item.spatial ? item.geometry_type : 'Geen kaartgeometrie');
            copy.append(name, detail);
            row.append(toggle);

            if (item.spatial) {
                const jump = document.createElement('button');
                jump.type = 'button';
                jump.className = 'item-jump';
                jump.setAttribute('aria-label', `${item.name} op de kaart tonen`);
                const cue = document.createElement('span');
                cue.className = 'jump-cue';
                cue.textContent = 'Kaart';
                jump.append(copy, cue);
                jump.onclick = () => {
                    if (!checkbox.checked) {
                        checkbox.checked = true;
                        updateItemSelection();
                    }
                    $$('.item-row.is-focused').forEach(itemRow => {
                        itemRow.classList.remove('is-focused');
                    });
                    row.classList.add('is-focused');
                    focusScenarioItem(item.key);
                };
                row.append(jump);
            } else {
                row.classList.add('non-spatial');
                row.append(copy);
            }
            list.append(row);
        });
        group.append(list);
        container.append(group);

        groupCheck.onchange = () => {
            itemCheckboxes()
                .filter(input => input.dataset.component === component)
                .forEach(input => { input.checked = groupCheck.checked; });
            updateItemSelection();
        };
    });

    itemCheckboxes().forEach(input => { input.onchange = updateItemSelection; });
    $('#itemSearch').value = '';
    updateItemSelection();
}

function fillSelect(select, items, valueKey, labelKey) {
    select.replaceChildren(...items.map(item => {
        const option = document.createElement('option');

        option.value = typeof valueKey === 'function' ? valueKey(item) : item[valueKey];
        option.textContent = typeof labelKey === 'function' ? labelKey(item) : item[labelKey];
        return option;
    }));
}

function toast(message) {
    const element = $('#toast');

    element.textContent = message;
    element.classList.add('show');
    setTimeout(() => element.classList.remove('show'), 4200);
}

function dossierPayload() {
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

function step(number) {
    $$('.panel').forEach(panel => panel.classList.remove('active'));
    $('#step' + number).classList.add('active');
    $$('.steps button').forEach(button => {
        button.classList.toggle('active', +button.dataset.step === number);
    });
    scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

function payload() {
    if (source === 'demo') {
        return {
            source,
            project_id: $('#project').value,
            scenario_id: $('#scenario').value
        };
    }

    if (source === 'tygron_project') {
        const project = liveProjects.find(
            item => item.file_name === $('#liveProject').value
        );

        return {
            source,
            base_url: $('#rootBaseUrl').value.trim(),
            domain: $('#domain').value.trim(),
            username: $('#username').value.trim(),
            login_key: $('#loginKey').value.trim(),
            project_file: $('#liveProject').value,
            project_name: project ? project.name : '',
            scenario_name: $('#liveScenario').value
        };
    }

    return {
        source,
        base_url: $('#baseUrl').value.trim(),
        token: $('#token').value.trim(),
        project_name: $('#projectName').value.trim(),
        scenario_name: $('#scenarioName').value.trim()
    };
}

function updateLiveScenarios() {
    const project = liveProjects.find(
        item => item.file_name === $('#liveProject').value
    );
    const scenarios = project ? project.versions : [];

    fillSelect(
        $('#liveScenario'),
        scenarios.map((name, index) => ({
            name,
            label: name + (index === project.active_version ? ' (actief)' : '')
        })),
        'name',
        'label'
    );
    $('#liveScenario').disabled = !scenarios.length;

    if (project && scenarios[project.active_version]) {
        $('#liveScenario').value = scenarios[project.active_version];
    }
}

async function loadTygronProjects() {
    const button = $('#loadProjects');
    const status = $('#projectLoadStatus');

    button.disabled = true;
    status.textContent = 'Projecten ophalen…';

    try {
        const data = await api('/api/tygron/projects', {
            base_url: $('#rootBaseUrl').value.trim(),
            domain: $('#domain').value.trim(),
            username: $('#username').value.trim(),
            login_key: $('#loginKey').value.trim()
        });

        liveProjects = data.projects;
        fillSelect($('#liveProject'), liveProjects, 'file_name', 'name');
        $('#liveProject').disabled = !liveProjects.length;
        status.textContent = `${liveProjects.length} projecten gevonden`;
        updateLiveScenarios();
    } catch (error) {
        liveProjects = [];
        $('#liveProject').innerHTML = '';
        $('#liveProject').disabled = true;
        $('#liveScenario').innerHTML = '';
        $('#liveScenario').disabled = true;
        status.textContent = '';
        toast(error.message);
    } finally {
        button.disabled = false;
    }
}

async function api(url, body) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    });
    const data = await response.json();

    if (!response.ok) {
        throw Error(data.error || 'Onbekende fout');
    }

    return data;
}

function updateScenarios() {
    const project = demo.projects.find(item => item.id === $('#project').value);

    fillSelect($('#scenario'), project.scenarios, 'id', 'name');
    updateNote();
}

function updateNote() {
    const project = demo.projects.find(item => item.id === $('#project').value);
    const scenario = project.scenarios.find(item => item.id === $('#scenario').value);

    $('#scenarioNote').textContent = scenario.description;
}

async function inspect() {
    const button = $('#inspect');

    button.disabled = true;
    button.textContent = 'Controleren…';

    try {
        inspected = await api('/api/inspect', payload());
        $('#selectionTitle').textContent = `${inspected.project} · ${inspected.scenario}`;
        if (!$('#recordReference').value.trim()) {
            $('#recordReference').value = defaultReference(
                inspected.project,
                inspected.scenario
            );
        }
        $('#summary').innerHTML = Object.entries(inspected.counts)
            .map(([key, value]) => `
                <div class="stat">
                    <b>${value}</b>
                    <span>${labels[key]}</span>
                </div>
            `)
            .join('');
        $('#spatialCount').textContent = `${inspected.spatial} ruimtelijke objecten`;
        renderItemSelector(inspected.items || []);

        if (inspected.warnings.length) {
            toast(inspected.warnings.join(' '));
        }

        step(2);
        await drawScenarioMap(inspected.preview);
        updateItemSelection();
    } catch (error) {
        toast(error.message);
    } finally {
        button.disabled = false;
        button.innerHTML = 'Verbinding controleren';
    }
}

async function doExport() {
    const button = $('#export');

    button.disabled = true;
    button.textContent = 'Dossier opbouwen…';

    try {
        const exportPayload = {
            ...payload(),
            notes: $('#notes').value,
            dossier: dossierPayload(),
            components: componentOrder.filter(component =>
                itemCheckboxes().some(input =>
                    input.dataset.component === component && input.checked
                )
            ),
            selected_items: selectedItems(),
            rasters: true
        };
        const data = await api('/api/export', exportPayload);

        $('#doneText').textContent =
            `${data.summary.project} · ${data.summary.scenario} ` +
            'is gereed voor overdracht en archivering.';
        const validationRow = data.summary.validation
            ? `
                <span>Automatische validatie</span>
                <b>${data.summary.validation}</b>
            `
            : '';

        $('#package').innerHTML = `
            <b>${data.filename}</b>
            <span>${(data.summary.size / 1024).toFixed(1)} KB</span>
            <span>Bestandsformaat</span>
            <b>ZIP + GeoPackage + HTML-rapport</b>
            <span>Integriteitscontrole</span>
            <b>SHA-256</b>
            ${validationRow}
        `;
        $('#download').href = data.download;

        if (data.summary.warnings.length) {
            toast(data.summary.warnings.join(' '));
        }

        step(3);
    } catch (error) {
        toast(error.message);
    } finally {
        button.disabled = itemCheckboxes().every(input => !input.checked);
        button.innerHTML = 'Dossier maken';
    }
}

async function init() {
    $('#decisionDate').value = new Intl.DateTimeFormat('sv-SE').format(new Date());
    try {
        demo = await fetch('/api/demo').then(response => response.json());
        fillSelect($('#project'), demo.projects, 'id', 'name');
        updateScenarios();
    } catch (error) {
        toast('Demonstratiedata kon niet worden geladen.');
    }
}

$$('.source-tabs button').forEach(button => {
    button.onclick = () => {
        $$('.source-tabs button').forEach(item => item.classList.remove('active'));
        button.classList.add('active');
        source = button.dataset.source;
        $('#demoFields').classList.toggle('hidden', source !== 'demo');
        $('#tygronFields').classList.toggle('hidden', source !== 'tygron');
        $('#tygronProjectFields').classList.toggle(
            'hidden',
            source !== 'tygron_project'
        );
    };
});

$('#project').onchange = updateScenarios;
$('#scenario').onchange = updateNote;
$('#inspect').onclick = inspect;
$('#export').onclick = doExport;
$('#loadProjects').onclick = loadTygronProjects;
$('#liveProject').onchange = updateLiveScenarios;
$('#itemSearch').oninput = filterItems;
$('#selectAll').onclick = () => {
    itemCheckboxes().forEach(input => { input.checked = true; });
    updateItemSelection();
};
$('#selectNone').onclick = () => {
    itemCheckboxes().forEach(input => { input.checked = false; });
    updateItemSelection();
};
$$('.back').forEach(button => {
    button.onclick = () => step(1);
});
$('#again').onclick = () => step(1);

init();
