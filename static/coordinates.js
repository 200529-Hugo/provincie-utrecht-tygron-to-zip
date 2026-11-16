import {t} from './i18n.js';

const CRS_LABELS = {
    'EPSG:4326': 'WGS 84 (EPSG:4326)',
    'EPSG:28992': 'RD New (EPSG:28992)'
};

export function crsLabel(crs) {
    return CRS_LABELS[crs] || crs;
}

export function sourceCrsLabel(crs) {
    return crs ? t('Bron-CRS: {crs}', {crs: crsLabel(crs)}) : t('Project-CRS onbekend');
}
