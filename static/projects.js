import {t} from './i18n.js';
import {getDemoProjects, getAccountProjects, getDemoThumbnail, getProjectThumbnail} from './api/projects.js';
import {catalogProjects, filterProjects, projectWorkflowUrl} from './project-catalog.js';
import {ThumbnailQueue} from './thumbnail-queue.js';

const list = document.querySelector('#projectList');
if (list) {
    let projects = [];
    let loadState = 'loading';
    const demoMode = list.dataset.source === 'demo';
    const thumbnailCache = new Map();
    const thumbnailQueue = new ThumbnailQueue(list.dataset.thumbnailConcurrency);
    let stopped = false;

    function showThumbnail(visual, url) {
        visual.classList.remove('thumbnail-loading');
        if (!url) {
            visual.title = t('Geen thumbnail beschikbaar.');
            return;
        }
        const image = document.createElement('img');
        image.alt = '';
        image.width = 320;
        image.height = 200;
        image.decoding = 'async';
        image.onerror = () => {
            visual.replaceChildren(document.createTextNode(visual.dataset.initials));
            visual.classList.remove('has-thumbnail');
            visual.title = t('Geen thumbnail beschikbaar.');
            URL.revokeObjectURL(url);
            thumbnailCache.set(visual.dataset.projectFile, null);
        };
        image.src = url;
        visual.replaceChildren(image);
        visual.classList.add('has-thumbnail');
        visual.title = t('2D-kaart van het project');
    }

    async function fetchThumbnail(project, signal) {
        const blob = demoMode
            ? await getDemoThumbnail({project_id: project.file_name}, signal)
            : await getProjectThumbnail({project_file: project.file_name}, signal);
        let url = null;
        if (blob) {
            if (stopped || signal.aborted) throw new DOMException('Cancelled', 'AbortError');
            url = URL.createObjectURL(blob);
        }
        if (stopped || signal.aborted) throw new DOMException('Cancelled', 'AbortError');
        thumbnailCache.set(project.file_name, url);
        return url;
    }

    function loadThumbnail(visual) {
        const project = {file_name: visual.dataset.projectFile};
        if (thumbnailCache.has(project.file_name)) {
            showThumbnail(visual, thumbnailCache.get(project.file_name));
            return;
        }
        visual.classList.add('thumbnail-loading');
        visual.title = t('Kaartafbeelding laden…');
        thumbnailQueue.enqueue(project.file_name, signal => fetchThumbnail(project, signal))
            .then(url => { if (!stopped && visual.isConnected) showThumbnail(visual, url); })
            .catch(error => {
                if (error.name === 'AbortError') return;
                // Een ontbrekende afbeelding mag de projectkeuze niet blokkeren.
                thumbnailCache.set(project.file_name, null);
                if (!stopped && visual.isConnected) showThumbnail(visual, null);
            });
    }

    const thumbnailObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!entry.target.isConnected) return;
            if (entry.isIntersecting) loadThumbnail(entry.target);
            else if (thumbnailQueue.cancel(entry.target.dataset.projectFile)) {
                entry.target.classList.remove('thumbnail-loading');
            }
        });
    }, {rootMargin: '80px'});
    window.addEventListener('pagehide', event => {
        if (event.persisted) return;
        stopped = true;
        thumbnailQueue.close();
        thumbnailObserver.disconnect();
        thumbnailCache.forEach(url => { if (url) URL.revokeObjectURL(url); });
    });
    const status = document.querySelector('#projectsStatus');
    const search = document.querySelector('#projectSearch');
    const refresh = document.querySelector('#refreshProjects');
    function render() {
        if (loadState !== 'ready') return;
        const matches = filterProjects(projects, search.value);
        thumbnailObserver.disconnect();
        thumbnailQueue.clearQueued();
        list.replaceChildren();
        status.textContent = !projects.length ? t('Er zijn geen beschikbare projecten.') : !matches.length ? t('Geen projecten gevonden voor deze zoekopdracht.') : (matches.length === 1 ? t('1 project') : t('{count} projecten', {count: matches.length}));
        matches.forEach((project, index) => {
            const row = document.createElement('button');
            row.className = 'project-row';
            const visual = document.createElement('span');
            visual.className = `project-visual visual-${index % 3}`;
            visual.setAttribute('aria-hidden', 'true');
            visual.textContent = project.name.slice(0, 2).toUpperCase();
            visual.dataset.initials = visual.textContent;
            visual.dataset.projectFile = project.file_name;
            const copy = document.createElement('span');
            copy.className = 'project-copy';
            const title = document.createElement('strong');
            title.textContent = project.name;
            title.dataset.sourceContent = 'true';
            const detail = document.createElement('small');
            if (project.description || project.domain) detail.dataset.sourceContent = 'true';
            detail.textContent = project.description || project.domain || (demoMode
                ? (project.scenarios.length === 1 ? t('1 scenario · Demonstratie') : t('{count} scenario’s · Demonstratie', {count: project.scenarios.length}))
                : t('Actieve versie'));
            const version = document.createElement('small');
            version.className = 'project-version';
            version.textContent = demoMode ? t('Offline beschikbaar') : t('Projectversie: {version}', {version: t(project.versions[0])});
            copy.append(title, detail, version);
            const arrow = document.createElement('span');
            arrow.className = 'project-arrow';
            arrow.setAttribute('aria-hidden', 'true');
            arrow.textContent = '→';
            row.append(visual, copy, arrow);
            row.setAttribute('aria-label', t('{name} selecteren', {name: project.name}));
            row.onclick = () => {
                if (!demoMode) sessionStorage.setItem('selectedProject', project.file_name);
                location.assign(projectWorkflowUrl(project, demoMode));
            };
            list.append(row);
            if (thumbnailCache.has(project.file_name)) showThumbnail(visual, thumbnailCache.get(project.file_name));
            else thumbnailObserver.observe(visual);
        });
    }
    async function load() {
        refresh.disabled = true;
        search.disabled = true;
        loadState = 'loading';
        list.setAttribute('aria-busy', 'true');
        status.setAttribute('role', 'status');
        status.textContent = t('Projecten ophalen…');
        list.replaceChildren();
        try {
            const response = demoMode ? await getDemoProjects() : await getAccountProjects();
            projects = catalogProjects(demoMode ? response : response.projects, demoMode);
            loadState = 'ready';
            render();
        } catch (error) {
            projects = [];
            loadState = 'error';
            status.setAttribute('role', 'alert');
            status.textContent = error.message;
        } finally {
            refresh.disabled = false;
            search.disabled = false;
            list.setAttribute('aria-busy', 'false');
        }
    }
    document.addEventListener('languagechange', render);
    search.oninput = render;
    refresh.onclick = () => {
        thumbnailCache.forEach((url, file) => { if (!url) thumbnailCache.delete(file); });
        load();
    };
    load();
}
