export const componentOrder = ['overlays', 'indicators', 'measures', 'alerts'];
export const selectionKey = (component, key) => `${component}:${key}`;
export const isOnMap = item => Boolean(item.spatial) && ['measures', 'alerts'].includes(item.component);
const normalized = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();

export function matchesItem(item, filters, checked) {
    const query = normalized(filters.query).trim();
    return (!filters.component || filters.component === 'all' || item.component === filters.component)
        && (filters.selection !== 'selected' || checked)
        && (filters.selection !== 'unselected' || !checked)
        && (!filters.spatialOnly || isOnMap(item))
        && (!query || normalized([item.name, item.detail, item.component, item.componentLabel].join(' ')).includes(query));
}

export function selectedItemKeys(inputs) {
    return new Set(inputs.filter(input => input.checked).map(input => selectionKey(input.component, input.key)));
}
