// De projectlijst bevat brongegevens en geen inloggegevens.
export function catalogProjects(projects, demoMode = false) {
    return projects.map(project => demoMode ? {
        file_name: project.id,
        name: project.name,
        description: '',
        scenarios: project.scenarios || []
    } : project);
}

export function filterProjects(projects, query) {
    const normalized = query.trim().toLocaleLowerCase();
    return projects.filter(project => project.name.toLocaleLowerCase().includes(normalized));
}

export function projectWorkflowUrl(project, demoMode = false) {
    if (!demoMode) return '/workflow?mode=account';
    const parameters = new URLSearchParams({mode: 'demo', project_id: project.file_name});
    if (project.scenarios[0]) parameters.set('scenario_id', project.scenarios[0].id);
    return `/workflow?${parameters}`;
}
