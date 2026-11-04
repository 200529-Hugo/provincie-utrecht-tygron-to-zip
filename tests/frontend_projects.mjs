import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source = await readFile(new URL('../static/project-catalog.js', import.meta.url), 'utf8');
const {catalogProjects, filterProjects, projectWorkflowUrl} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const projects = [
    {file_name: 'station', name: 'Stationsgebied Utrecht', versions: ['Current'], description: 'Planning'},
    {file_name: 'river', name: 'Kromme Rijngebied', versions: ['Active']}
];
assert.deepEqual(filterProjects(projects, '  STATION '), [projects[0]]);
assert.deepEqual(filterProjects(projects, 'missing'), []);
assert.deepEqual(filterProjects([], ''), []);
assert.equal(filterProjects(projects, '').length, 2);
assert.deepEqual(catalogProjects(projects), projects);
assert.equal(projectWorkflowUrl(projects[0]), '/workflow?mode=account');
const demo = catalogProjects([{id: 'demo project&1', name: 'Demo', scenarios: [{id: 'green&cool', name: 'Green'}]}], true)[0];
const url = new URL(projectWorkflowUrl(demo, true), 'http://localhost');
assert.equal(url.pathname, '/workflow');
assert.equal(url.searchParams.get('mode'), 'demo');
assert.equal(url.searchParams.get('project_id'), 'demo project&1');
assert.equal(url.searchParams.get('scenario_id'), 'green&cool');
assert.equal(url.searchParams.has('password'), false);
assert.equal(url.searchParams.has('login_key'), false);
console.log('Catalog search, empty results, account selection and demo selection pass.');
