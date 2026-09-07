const archiveInput = document.querySelector('#archiveInput');
const dropZone = document.querySelector('#dropZone');
const dropTitle = document.querySelector('#dropTitle');
const dropDetail = document.querySelector('#dropDetail');
const validateButton = document.querySelector('#validateButton');
const validationResult = document.querySelector('#validationResult');
const toastElement = document.querySelector('#toast');
let selectedFile;

function formatBytes(bytes) {
    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function toast(message) {
    toastElement.textContent = message;
    toastElement.classList.add('show');
    setTimeout(() => toastElement.classList.remove('show'), 4200);
}

function selectFile(file) {
    if (!file) {
        return;
    }
    if (!file.name.toLowerCase().endsWith('.zip')) {
        toast('Selecteer een ZIP-bestand.');
        return;
    }
    if (file.size > 200_000_000) {
        toast('Het ZIP-dossier is groter dan 200 MB.');
        return;
    }
    selectedFile = file;
    dropTitle.textContent = file.name;
    dropDetail.textContent = `${formatBytes(file.size)} · gereed voor controle`;
    dropZone.classList.add('has-file');
    validateButton.disabled = false;
    validationResult.classList.add('hidden');
}

function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) {
        element.className = className;
    }
    if (text !== undefined) {
        element.textContent = text;
    }
    return element;
}

function renderResult(report) {
    const approved = report.status === 'goedgekeurd';
    const resultMark = document.querySelector('#resultMark');
    const counts = document.querySelector('#resultCounts');
    const checks = document.querySelector('#checkList');

    validationResult.classList.remove('hidden', 'approved', 'rejected');
    validationResult.classList.add(approved ? 'approved' : 'rejected');
    resultMark.textContent = approved ? 'OK' : '!';
    document.querySelector('#resultLabel').textContent = approved ? 'Goedgekeurd' : 'Afgekeurd';
    document.querySelector('#resultTitle').textContent = approved
        ? 'Het dossier is compleet en ongewijzigd.'
        : 'Er zijn afwijkingen in het dossier gevonden.';
    document.querySelector('#resultContext').textContent =
        [report.project, report.scenario, selectedFile.name].filter(Boolean).join(' · ');

    counts.replaceChildren();
    Object.entries(report.components || {}).forEach(([name, value]) => {
        const item = createElement('div', 'result-count');
        item.append(createElement('b', '', value));
        item.append(createElement('span', '', name));
        counts.append(item);
    });

    checks.replaceChildren();
    report.checks.forEach(check => {
        const item = createElement('div', `check-row ${check.status}`);
        item.append(createElement('span', 'check-state', check.status === 'ok' ? 'OK' : '!'));
        const text = createElement('div');
        text.append(createElement('b', '', check.check));
        text.append(createElement('small', '', check.detail));
        item.append(text);
        checks.append(item);
    });
}

async function validateArchive() {
    if (!selectedFile) {
        return;
    }
    validateButton.disabled = true;
    validateButton.textContent = 'Dossier wordt gecontroleerd…';
    try {
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: {'Content-Type': 'application/zip'},
            body: selectedFile
        });
        const report = await response.json();
        if (!response.ok) {
            throw Error(report.error || 'De controle is mislukt.');
        }
        renderResult(report);
        validationResult.scrollIntoView({behavior: 'smooth', block: 'start'});
    } catch (error) {
        toast(error.message);
    } finally {
        validateButton.disabled = false;
        validateButton.textContent = 'Opnieuw controleren';
    }
}

archiveInput.addEventListener('change', event => selectFile(event.target.files[0]));
['dragenter', 'dragover'].forEach(type => {
    dropZone.addEventListener(type, event => {
        event.preventDefault();
        dropZone.classList.add('dragging');
    });
});
['dragleave', 'drop'].forEach(type => {
    dropZone.addEventListener(type, event => {
        event.preventDefault();
        dropZone.classList.remove('dragging');
    });
});
dropZone.addEventListener('drop', event => selectFile(event.dataTransfer.files[0]));
validateButton.addEventListener('click', validateArchive);
