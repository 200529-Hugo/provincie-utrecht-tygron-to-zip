import {t} from '../i18n.js';
import {getDemoProjects, getAccountProjects, getLegacyProjects} from '../api/projects.js';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];

// Alleen de bronkeuze en verbindingsvelden horen in dit onderdeel.
export function createSourceForm({mode, parameters, onScenarioChanged, onError}) {
    let source = mode === 'tygron' ? 'tygron' : 'demo';
    let projects = [];
    let liveProjects = [];
    const accountMode = mode === 'account';
    function fillSelect(select, items, valueKey, labelKey) {
        select.replaceChildren(...items.map(item => {
            const option = document.createElement('option');

            if (select.id === 'project' || select.id === 'scenario' || select.id === 'liveProject') option.dataset.sourceContent = 'true';
            option.value = typeof valueKey === 'function' ? valueKey(item) : item[valueKey];
            option.textContent = t(typeof labelKey === 'function' ? labelKey(item) : item[labelKey]);
            return option;
        }));
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
                authenticated: accountMode,
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
        status.textContent = t('Projecten ophalen…');

        try {
            const data = await getLegacyProjects({
                base_url: $('#rootBaseUrl').value.trim(),
                domain: $('#domain').value.trim(),
                username: $('#username').value.trim(),
                login_key: $('#loginKey').value.trim()
            });

            liveProjects = data.projects;
            fillSelect($('#liveProject'), liveProjects, 'file_name', 'name');
            $('#liveProject').disabled = !liveProjects.length;
            status.textContent = t('{count} projecten gevonden', {count: liveProjects.length});
            updateLiveScenarios();
        } catch (error) {
            liveProjects = [];
            $('#liveProject').innerHTML = '';
            $('#liveProject').disabled = true;
            $('#liveScenario').innerHTML = '';
            $('#liveScenario').disabled = true;
            status.textContent = '';
            onError(error.message);
        } finally {
            button.disabled = false;
        }
    }

    function updateScenarios() {
        const project = projects.find(item => item.id === $('#project').value);

        if (!project) return;
        fillSelect($('#scenario'), project.scenarios, 'id', 'name');
        updateNote();
    }

    function updateNote() {
        const project = projects.find(item => item.id === $('#project').value);
        if (!project) return;
        const scenario = project.scenarios.find(item => item.id === $('#scenario').value);

        $('#scenarioNote').textContent = t(scenario?.description || '');
    }

    async function initialize() {
        if (mode === 'tygron') return false;
        if (accountMode) {
            liveProjects = (await getAccountProjects()).projects;
            const selected = sessionStorage.getItem('selectedProject');
            const project = liveProjects.find(item => item.file_name === selected);
            if (!project) { location.assign('/projecten'); return false; }
            source = 'tygron_project';
            fillSelect($('#liveProject'), liveProjects, 'file_name', 'name');
            $('#liveProject').value = selected;
            updateLiveScenarios();
            $('#demoFields').classList.add('hidden');
            $('.source-tabs').classList.add('hidden');
            return true;
        }
        projects = await getDemoProjects();
        fillSelect($('#project'), projects, 'id', 'name');
        updateScenarios();
        if (mode === 'demo' && parameters.has('project_id')) {
            const project = projects.find(item => item.id === parameters.get('project_id'));
            if (!project) { location.assign('/projecten?mode=demo'); return false; }
            $('#project').value = project.id;
            updateScenarios();
            const scenario = project.scenarios.find(item => item.id === parameters.get('scenario_id')) || project.scenarios[0];
            if (!scenario) { location.assign('/projecten?mode=demo'); return false; }
            $('#scenario').value = scenario.id;
            fillSelect($('#reviewScenario'), project.scenarios, 'id', 'name');
            $('#reviewScenario').value = scenario.id;
            $('#reviewScenarioField').classList.remove('hidden');
            return true;
        }
        if (mode === 'legacy') $('[data-source="tygron_project"]').click();
        return false;
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

    $('#project')?.addEventListener('change', updateScenarios);
    $('#scenario')?.addEventListener('change', updateNote);
    $('#loadProjects')?.addEventListener('click', loadTygronProjects);
    $('#liveProject')?.addEventListener('change', updateLiveScenarios);
    $('#reviewScenario').onchange = () => {
        $('#scenario').value = $('#reviewScenario').value;
        updateNote();
        onScenarioChanged();
    };
    if ($('#showSessionToken')) {
        $('#showSessionToken').onclick = event => {
            const visible = $('#token').type === 'password';
            $('#token').type = visible ? 'text' : 'password';
            event.currentTarget.setAttribute('aria-pressed', String(visible));
            event.currentTarget.textContent = t(visible ? 'Verbergen' : 'Tonen');
        };
    }
    return {initialize, payload};
}
