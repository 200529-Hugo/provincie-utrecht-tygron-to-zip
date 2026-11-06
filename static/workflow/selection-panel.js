import {t} from '../i18n.js';
import {componentOrder, selectionKey, selectedItemKeys, matchesItem, isOnMap} from '../review-selection.js';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];

// Dit onderdeel beheert alleen de onderdelenlijst, filters en checkboxselectie.
export function createSelectionPanel({onChange, onShowOnMap}) {
    const labels = {
        get overlays() { return t('overlays'); },
        get indicators() { return t('indicatoren'); },
        get measures() { return t('maatregelen'); },
        get alerts() { return t('alerts'); }
    };
    const bulkButton = $('#toggleResults');
    let componentFilter = 'all';
    let allResultsSelected = false;
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
        $('#selectionCount').textContent = t('{selected} van {total} geselecteerd', {selected: checked.length, total: inputs.length});
        $('#selectionTabCount').textContent = checked.length;
        $('#exportSelectionCount').textContent = checked.length
            ? t('{count} onderdelen in je dossier', {count: checked.length}) : t('Geen onderdelen geselecteerd');
        $('#spatialCount').textContent = t('{selected} van {total} ruimtelijke objecten', {selected: selectedSpatial.length, total: spatial.length});
        onChange(checked.length, selectedItemKeys(inputs.map(input => ({
            component: input.dataset.component, key: input.dataset.itemKey, checked: input.checked
        }))));
        filterItems();
    }

    function setGroupExpanded(group, expanded) {
        group.querySelector('.item-list').hidden = !expanded;
        group.querySelector('.group-disclosure').setAttribute('aria-expanded', String(expanded));
    }

    function filterItems(expandMatches = false) {
        const filters = {query: $('#itemSearch').value, component: componentFilter,
            selection: $('#selectionFilter').value, spatialOnly: $('#spatialOnly').checked};
        let totalVisible = 0;
        let totalSelected = 0;
        $$('.item-group').forEach(group => {
            const visible = [];
            group.querySelectorAll('.item-row').forEach(row => {
                const checkbox = row.querySelector('input[data-item-key]');
                const item = {name: row.dataset.name, detail: row.dataset.detail,
                    component: checkbox.dataset.component, componentLabel: labels[checkbox.dataset.component],
                    spatial: checkbox.dataset.spatial === 'true'};
                row.hidden = !matchesItem(item, filters, checkbox.checked);
                if (!row.hidden) visible.push(checkbox);
            });
            group.hidden = visible.length === 0;
            totalVisible += visible.length;
            const check = group.querySelector('input[data-group]');
            const selected = visible.filter(input => input.checked).length;
            totalSelected += selected;
            check.checked = visible.length > 0 && selected === visible.length;
            check.indeterminate = selected > 0 && selected < visible.length;
            group.querySelector('[data-group-count]').textContent = `${selected}/${visible.length}`;
            if (expandMatches && visible.length) setGroupExpanded(group, true);
        });
        $('#filterResultCount').textContent = t('{count} resultaten', {count: totalVisible});
        $('#noItemResults').classList.toggle('hidden', totalVisible !== 0);
        allResultsSelected = totalVisible > 0 && totalSelected === totalVisible;
        bulkButton.disabled = totalVisible === 0;
        bulkButton.textContent = t(allResultsSelected ? 'Resultaten deselecteren' : 'Resultaten selecteren');
        $$('[data-component-filter]').forEach(button => {
            button.setAttribute('aria-pressed', String(button.dataset.componentFilter === componentFilter));
        });
    }

    function clearFilters() {
        componentFilter = 'all';
        $('#itemSearch').value = '';
        $('#selectionFilter').value = 'all';
        $('#spatialOnly').checked = false;
        filterItems();
    }

    function selectResults(checked, component) {
        $$('#itemGroups .item-row:not([hidden]) input[data-item-key]').forEach(input => {
            if (!component || input.dataset.component === component) input.checked = checked;
        });
        updateItemSelection();
    }

    function renderCategoryFilters(counts) {
        const filters = [{key: 'all', name: t('Alles'), count: Object.values(counts).reduce((a, b) => a + b, 0)},
            ...componentOrder.map(key => ({key, name: labels[key], count: counts[key] || 0}))];
        $('#summary').replaceChildren(...filters.map(filter => {
            const button = document.createElement('button');
            button.type = 'button';
            button.dataset.componentFilter = filter.key;
            const name = document.createElement('span');
            name.textContent = filter.name;
            const count = document.createElement('b');
            count.textContent = filter.count;
            button.append(name, count);
            button.onclick = () => { componentFilter = filter.key; filterItems(true); };
            return button;
        }));
    }

    function renderItemSelector(items) {
        const container = $('#itemGroups');
        container.replaceChildren();
        componentOrder.forEach(component => {
            const componentItems = items.filter(item => item.component === component);
            if (!componentItems.length) return;
            const group = document.createElement('section');
            group.className = 'item-group';
            const heading = document.createElement('div');
            heading.className = 'item-group-head';
            const groupLabel = document.createElement('label');
            groupLabel.className = 'item-group-toggle';
            const groupCheck = document.createElement('input');
            groupCheck.type = 'checkbox';
            groupCheck.checked = true;
            groupCheck.dataset.group = component;
            groupCheck.setAttribute('aria-label', t('Zoekresultaten in {type} selecteren', {type: labels[component]}));
            const title = document.createElement('strong');
            title.textContent = labels[component];
            const count = document.createElement('small');
            count.dataset.groupCount = component;
            groupLabel.append(groupCheck);
            const collapse = document.createElement('button');
            collapse.type = 'button';
            collapse.className = 'group-disclosure';
            const chevron = document.createElement('span');
            chevron.className = 'chevron chevron--down';
            chevron.setAttribute('aria-hidden', 'true');
            collapse.append(title, count, chevron);
            collapse.setAttribute('aria-expanded', 'true');
            collapse.setAttribute('aria-controls', `items-${component}`);
            heading.append(groupLabel, collapse);
            group.append(heading);
            const list = document.createElement('div');
            list.className = 'item-list';
            list.id = `items-${component}`;
            collapse.onclick = () => setGroupExpanded(group, list.hidden);
            componentItems.forEach(item => {
                const row = document.createElement('div');
                row.className = 'item-row';
                row.dataset.name = item.name;
                row.dataset.detail = item.detail;
                const toggle = document.createElement('label');
                toggle.className = 'item-toggle';
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.checked = true;
                checkbox.dataset.itemKey = item.key;
                checkbox.dataset.component = component;
                checkbox.dataset.spatial = String(isOnMap(item));
                checkbox.setAttribute('aria-label', t('{name} opnemen in het dossier', {name: item.name}));
                const copy = document.createElement('span');
                copy.className = 'item-copy';
                const name = document.createElement('strong');
                name.textContent = item.name;
                name.dataset.sourceContent = 'true';
                const detail = document.createElement('small');
                if (item.detail) detail.dataset.sourceContent = 'true';
                detail.textContent = item.detail || (isOnMap(item) ? item.geometry_type : t('Niet op de kaart'));
                copy.append(name, detail);
                toggle.append(checkbox, copy);
                row.append(toggle);
                if (isOnMap(item)) {
                    const jump = document.createElement('button');
                    jump.type = 'button';
                    jump.className = 'item-jump';
                    jump.textContent = t('Kaart');
                    jump.setAttribute('aria-label', t('{name} op de kaart tonen', {name: item.name}));
                    jump.onclick = async () => {
                        await onShowOnMap(selectionKey(component, item.key));
                        $$('.item-row.is-focused').forEach(itemRow => itemRow.classList.remove('is-focused'));
                        row.classList.add('is-focused');
                    };
                    row.append(jump);
                }
                checkbox.onchange = updateItemSelection;
                list.append(row);
            });
            group.append(list);
            container.append(group);
            groupCheck.onchange = () => selectResults(groupCheck.checked, component);
        });
        updateItemSelection();
    }

    $('#itemSearch').oninput = () => filterItems(true);
    bulkButton.onclick = () => selectResults(!allResultsSelected);
    $('#selectionFilter').onchange = () => filterItems(true);
    $('#spatialOnly').onchange = () => filterItems(true);
    $('#clearFilters').onclick = clearFilters;
    $('#resetItemSearch').onclick = clearFilters;
    return {
        renderCategories: renderCategoryFilters,
        renderItems: renderItemSelector,
        refresh: updateItemSelection,
        selectedItems,
        selectedComponents: () => componentOrder.filter(component =>
            itemCheckboxes().some(input => input.dataset.component === component && input.checked)),
    };
}
