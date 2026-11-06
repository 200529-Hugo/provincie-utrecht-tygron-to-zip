import {t} from '../i18n.js';
import {getDemoProjects, getAccountProjects, getLegacyProjects} from '../api/projects.js';

const $ = selector => document.querySelector(selector);

function fillSelect(select, items, value, label) {
    select.replaceChildren(...items.map((item, index) => {
        const option = new Option(label(item, index), value(item));
        option.dataset.sourceContent = 'true';
        return option;
    }));
}

// Dit onderdeel beheert de brongegevens voor controle en export.
export function createSourceForm({mode, parameters, onScenarioChanged, onConnectionChanged}) {
    let project;
    const accountMode = mode === 'account';
    const demoMode = mode === 'demo';
    const reviewScenario = $('#reviewScenario');
    const legacyForm = $('#loginKeyForm');

    function legacyCredentials() {
        return {
            base_url: $('#rootBaseUrl').value.trim(),
            domain: $('#domain').value.trim(),
            username: $('#username').value.trim(),
            login_key: $('#loginKey').value.trim()
        };
    }

    function payload() {
        if (demoMode) return {source: 'demo', project_id: project.id, scenario_id: reviewScenario.value};
        if (accountMode || legacyForm) {
            const activeVersion = project.versions[project.active_version] ?? project.versions[0] ?? '';
            return {
                ...(legacyForm ? legacyCredentials() : {}),
                source: 'tygron_project',
                authenticated: accountMode,
                project_file: project.file_name,
                project_name: project.name,
                scenario_name: accountMode ? activeVersion : $('#liveScenario').value
            };
        }
        return {
            source: 'tygron',
            base_url: $('#baseUrl').value.trim(),
            token: $('#token').value.trim(),
            project_name: $('#projectName').value.trim(),
            scenario_name: $('#scenarioName').value.trim()
        };
    }

    async function initialize() {
        if (accountMode) {
            const {projects} = await getAccountProjects();
            project = projects.find(item => item.file_name === sessionStorage.getItem('selectedProject'));
            if (!project) location.assign('/projecten');
            return Boolean(project);
        }
        if (demoMode) {
            const projects = await getDemoProjects();
            project = projects.find(item => item.id === parameters.get('project_id'));
            if (!project?.scenarios.length) {
                location.assign('/projecten?mode=demo');
                return false;
            }
            fillSelect(reviewScenario, project.scenarios, item => item.id, item => item.name);
            if (project.scenarios.some(item => item.id === parameters.get('scenario_id'))) {
                reviewScenario.value = parameters.get('scenario_id');
            }
            $('#reviewScenarioField').classList.remove('hidden');
        }
        return demoMode;
    }

    if (legacyForm) {
        const credentials = $('#loginKeyCredentials');
        const load = $('#loadProjects');
        const status = $('#projectLoadStatus');
        const errorMessage = $('#sessionConnectionStatus');
        const projectSelect = $('#liveProject');
        const scenarioSelect = $('#liveScenario');
        const inspect = $('#inspect');
        let projects = [];

        function updateProject() {
            project = projects.find(item => item.file_name === projectSelect.value);
            const versions = project?.versions || [];
            fillSelect(scenarioSelect, versions, name => name,
                (name, index) => name + (index === project.active_version ? ' ' + t('(actief)') : ''));
            if (versions[project?.active_version]) scenarioSelect.value = versions[project.active_version];
            scenarioSelect.disabled = !versions.length;
            inspect.disabled = !project;
        }

        function clearProjects() {
            projects = [];
            projectSelect.replaceChildren();
            projectSelect.disabled = true;
            updateProject();
            status.textContent = '';
        }

        credentials.addEventListener('input', clearProjects);
        projectSelect.onchange = updateProject;
        load.onclick = async () => {
            if (!Array.from(credentials.querySelectorAll('input')).every(input => input.reportValidity())) return;
            const values = legacyCredentials();
            clearProjects();
            onConnectionChanged();
            status.textContent = t('Projecten ophalen…');
            credentials.disabled = load.disabled = true;
            try {
                ({projects} = await getLegacyProjects(values));
                fillSelect(projectSelect, projects, item => item.file_name, item => item.name);
                projectSelect.disabled = !projects.length;
                status.textContent = t('{count} projecten gevonden', {count: projects.length});
                updateProject();
            } catch (error) {
                status.textContent = '';
                errorMessage.textContent = error.message;
            } finally {
                credentials.disabled = load.disabled = false;
            }
        };
        load.disabled = false;
    }

    reviewScenario.onchange = onScenarioChanged;
    return {initialize, payload};
}
