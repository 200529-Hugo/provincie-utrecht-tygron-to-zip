import {
    drawScenarioMap,
    focusScenarioItem,
    setScenarioSelection
} from './scenario-map.js';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];

function updateScenarios(projectId) {
    const project = demo.projects.find(item => item.id === projectId);

    fillSelect($('#scenario'), project.scenarios, 'id', 'name');
    updateNote();
}