import {
    LngLatBounds,
    Map,
    NavigationControl,
    Popup
} from './vendor/maplibre-gl.mjs';

const SOURCE_ID = 'scenario-objects';
const GROUPS = {
    measures: ['measure-polygons', 'measure-lines', 'measure-points'],
    alerts: ['alert-polygons', 'alert-lines', 'alert-points']
};

let scenarioMap;
let scenarioData = {type: 'FeatureCollection', features: []};

function blankStyle() {
    return {
        version: 8,
        sources: {},
        layers: [{
            id: 'background',
            type: 'background',
            paint: {'background-color': '#e9ece6'}
        }]
    };
}

function status(text, available) {
    const element = document.querySelector('#basemapStatus');
    element.textContent = text;
    element.classList.toggle('available', available);
}

async function resolveStyle() {
    try {
        const configResponse = await fetch('/api/map-config');
        const config = await configResponse.json();
        if (!config.style_url) {
            throw Error('Geen OpenMapTiles-stijl geconfigureerd.');
        }
        const response = await fetch(config.style_url, {
            signal: AbortSignal.timeout(1200)
        });
        if (!response.ok) {
            throw Error('TileServer GL is niet beschikbaar.');
        }
        const styleDocument = await response.json();
        const tileSource = Object.values(styleDocument.sources || {})
            .find(source => source.type === 'vector' && source.url);
        let coverage;

        if (tileSource) {
            const tileJsonUrl = new URL(tileSource.url, config.style_url).href;
            const tileJsonResponse = await fetch(tileJsonUrl, {
                signal: AbortSignal.timeout(1200)
            });
            if (tileJsonResponse.ok) {
                const tileJson = await tileJsonResponse.json();
                if (Array.isArray(tileJson.bounds) && tileJson.bounds.length === 4) {
                    coverage = tileJson.bounds.map(Number);
                }
            }
        }
        return {style: config.style_url, available: true, coverage};
    } catch (error) {
        return {style: blankStyle(), available: false};
    }
}

function dataBounds(data) {
    const coordinates = [];
    data.features.forEach(feature => coordinatesFromGeometry(feature.geometry, coordinates));
    if (!coordinates.length) {
        return {coordinates, bounds: null};
    }

    const west = Math.min(...coordinates.map(coordinate => coordinate[0]));
    const south = Math.min(...coordinates.map(coordinate => coordinate[1]));
    const east = Math.max(...coordinates.map(coordinate => coordinate[0]));
    const north = Math.max(...coordinates.map(coordinate => coordinate[1]));
    return {coordinates, bounds: [west, south, east, north]};
}

function coversScenario(coverage, bounds) {
    if (!coverage || !bounds) {
        return true;
    }
    return bounds[0] >= coverage[0] && bounds[1] >= coverage[1] &&
        bounds[2] <= coverage[2] && bounds[3] <= coverage[3];
}

function featureCollection(items) {
    const features = [];
    items.forEach(item => {
        const source = item.feature;
        const properties = {
            ...(source.properties || {}),
            component: item.component,
            selection_key: item.key
        };
        if (source.geometry.type === 'GeometryCollection') {
            source.geometry.geometries.forEach((geometry, index) => {
                features.push({
                    type: 'Feature',
                    geometry,
                    properties: {...properties, geometry_part: index + 1}
                });
            });
        } else {
            features.push({type: 'Feature', geometry: source.geometry, properties});
        }
    });
    return {type: 'FeatureCollection', features};
}

function coordinatesForFeature(feature) {
    const coordinates = [];
    coordinatesFromGeometry(feature.geometry, coordinates);
    return coordinates;
}

export function setScenarioSelection(keys) {
    if (!scenarioMap || !scenarioMap.getSource(SOURCE_ID)) {
        return;
    }
    scenarioMap.getSource(SOURCE_ID).setData({
        type: 'FeatureCollection',
        features: scenarioData.features.filter(feature => keys.has(feature.properties.selection_key))
    });
}

export function focusScenarioItem(key) {
    if (!scenarioMap) {
        return;
    }
    const features = scenarioData.features.filter(
        item => item.properties.selection_key === key
    );
    if (!features.length) {
        return;
    }
    const group = features[0].properties.component;
    (GROUPS[group] || []).forEach(layerId => {
        if (scenarioMap.getLayer(layerId)) {
            scenarioMap.setLayoutProperty(layerId, 'visibility', 'visible');
        }
    });
    const layerButton = document.querySelector(`[data-map-layer="${group}"]`);
    if (layerButton) {
        layerButton.setAttribute('aria-pressed', 'true');
    }

    const coordinates = features.flatMap(coordinatesForFeature);
    if (!coordinates.length) {
        return;
    }
    const bounds = coordinates.reduce(
        (result, coordinate) => result.extend(coordinate),
        new LngLatBounds(coordinates[0], coordinates[0])
    );
    const west = bounds.getWest();
    const east = bounds.getEast();
    const south = bounds.getSouth();
    const north = bounds.getNorth();
    if (west === east && south === north) {
        scenarioMap.easeTo({center: coordinates[0], zoom: 17, duration: 650});
    } else {
        scenarioMap.fitBounds(bounds, {padding: 72, maxZoom: 17, duration: 650});
    }
}

function coordinatesFromGeometry(geometry, output) {
    if (geometry.type === 'GeometryCollection') {
        geometry.geometries.forEach(item => coordinatesFromGeometry(item, output));
        return;
    }

    function collect(value) {
        if (Array.isArray(value) && typeof value[0] === 'number') {
            output.push(value);
        } else if (Array.isArray(value)) {
            value.forEach(collect);
        }
    }

    collect(geometry.coordinates);
}

function addScenarioLayers(map, data) {
    map.addSource(SOURCE_ID, {type: 'geojson', data});
    const measureFilter = ['==', ['get', 'component'], 'measures'];
    const alertFilter = ['==', ['get', 'component'], 'alerts'];

    map.addLayer({
        id: 'measure-polygons',
        type: 'fill',
        source: SOURCE_ID,
        filter: ['all', measureFilter, ['==', ['geometry-type'], 'Polygon']],
        paint: {'fill-color': '#ec0000', 'fill-opacity': 0.22, 'fill-outline-color': '#a90000'}
    });
    map.addLayer({
        id: 'measure-lines',
        type: 'line',
        source: SOURCE_ID,
        filter: ['all', measureFilter, ['==', ['geometry-type'], 'LineString']],
        paint: {'line-color': '#231b1b', 'line-width': 4, 'line-opacity': 0.9}
    });
    map.addLayer({
        id: 'measure-points',
        type: 'circle',
        source: SOURCE_ID,
        filter: ['all', measureFilter, ['==', ['geometry-type'], 'Point']],
        paint: {
            'circle-color': '#231b1b',
            'circle-radius': 7,
            'circle-stroke-color': '#fff',
            'circle-stroke-width': 2
        }
    });
    map.addLayer({
        id: 'alert-polygons',
        type: 'fill',
        source: SOURCE_ID,
        filter: ['all', alertFilter, ['==', ['geometry-type'], 'Polygon']],
        paint: {'fill-color': '#f6be00', 'fill-opacity': 0.38, 'fill-outline-color': '#ec0000'}
    });
    map.addLayer({
        id: 'alert-lines',
        type: 'line',
        source: SOURCE_ID,
        filter: ['all', alertFilter, ['==', ['geometry-type'], 'LineString']],
        paint: {'line-color': '#ec0000', 'line-width': 4, 'line-dasharray': [1.5, 1.2]}
    });
    map.addLayer({
        id: 'alert-points',
        type: 'circle',
        source: SOURCE_ID,
        filter: ['all', alertFilter, ['==', ['geometry-type'], 'Point']],
        paint: {
            'circle-color': '#ec0000',
            'circle-radius': 8,
            'circle-stroke-color': '#fff',
            'circle-stroke-width': 2.5
        }
    });
}

function popupHtml(properties) {
    const escape = value => String(value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;');
    const type = properties.component === 'alerts' ? 'Alert' : 'Maatregel';
    const statusText = properties.status || properties.severity || '';
    return `
        <div class="scenario-popup">
            <small>${type}</small>
            <strong>${escape(properties.name || 'Onbenoemd object')}</strong>
            ${statusText ? `<span>${escape(statusText)}</span>` : ''}
            ${properties.description ? `<p>${escape(properties.description)}</p>` : ''}
        </div>
    `;
}

function bindInteractions(map) {
    const layerIds = Object.values(GROUPS).flat();
    layerIds.forEach(layerId => {
        map.on('mouseenter', layerId, () => {
            map.getCanvas().style.cursor = 'pointer';
        });
        map.on('mouseleave', layerId, () => {
            map.getCanvas().style.cursor = '';
        });
        map.on('click', layerId, event => {
            const feature = event.features && event.features[0];
            if (!feature) {
                return;
            }
            new Popup({closeButton: true, maxWidth: '280px'})
                .setLngLat(event.lngLat)
                .setHTML(popupHtml(feature.properties || {}))
                .addTo(map);
        });
    });
}

function bindLayerButtons(map) {
    document.querySelectorAll('[data-map-layer]').forEach(button => {
        button.setAttribute('aria-pressed', 'true');
        button.onclick = () => {
            const group = button.dataset.mapLayer;
            const visible = button.getAttribute('aria-pressed') === 'true';
            GROUPS[group].forEach(layerId => {
                if (map.getLayer(layerId)) {
                    map.setLayoutProperty(layerId, 'visibility', visible ? 'none' : 'visible');
                }
            });
            button.setAttribute('aria-pressed', String(!visible));
        };
    });
}

export async function drawScenarioMap(items) {
    const container = document.querySelector('#map');
    if (scenarioMap) {
        scenarioMap.remove();
    }
    container.replaceChildren();

    if (!items.length) {
        container.className = 'map-empty';
        container.textContent = 'Geen ruimtelijke maatregelen of alerts in deze selectie.';
        status('Geen kaartobjecten', false);
        return;
    }

    container.className = '';
    const data = featureCollection(items);
    scenarioData = data;
    const spatial = dataBounds(data);
    status('OpenMapTiles zoeken', false);
    const resolved = await resolveStyle();
    const covered = resolved.available && coversScenario(resolved.coverage, spatial.bounds);
    status(
        !resolved.available
            ? 'Basiskaart niet actief'
            : covered ? 'OpenMapTiles actief' : 'Basiskaart dekt gebied niet',
        covered
    );
    scenarioMap = new Map({
        container,
        style: resolved.style,
        center: [5.12, 52.09],
        zoom: 11,
        attributionControl: true
    });
    scenarioMap.addControl(new NavigationControl({showCompass: false}), 'top-right');

    if (resolved.available) {
        await new Promise(resolve => scenarioMap.once('style.load', resolve));
    } else {
        // De lege stijl kan al tijdens de constructor klaar zijn. De korte
        // fallback voorkomt dat we een synchroon afgevuurd load-event missen.
        await Promise.race([
            new Promise(resolve => scenarioMap.once('load', resolve)),
            new Promise(resolve => window.setTimeout(resolve, 250))
        ]);
    }

    addScenarioLayers(scenarioMap, data);
    bindInteractions(scenarioMap);
    bindLayerButtons(scenarioMap);

    if (spatial.coordinates.length) {
        const bounds = spatial.coordinates.reduce(
            (result, coordinate) => result.extend(coordinate),
            new LngLatBounds(spatial.coordinates[0], spatial.coordinates[0])
        );
        scenarioMap.fitBounds(bounds, {padding: 48, maxZoom: 16, duration: 0});
    }

}
