const config = JSON.parse(document.querySelector('#languageConfig')?.textContent || '{}');
export let language = config.language || 'nl';
let catalog = config.catalog || {};
export function t(text, values = {}) {
    let translated = catalog[text] || text;
    Object.entries(values).forEach(([key, value]) => { translated = translated.replaceAll(`{${key}}`, String(value)); });
    return translated;
}

export function changeLanguage(nextLanguage, nextCatalog) {
    const previous = catalog;
    language = nextLanguage;
    catalog = nextCatalog;
    const exact = new Map(Object.entries(previous).map(([key, value]) => [value, key]));
    const escape = value => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const templates = Object.entries(previous).filter(([key]) => /\{\w+\}/.test(key)).map(([key, value]) => {
        const names = [];
        let pattern = '';
        let start = 0;
        for (const match of value.matchAll(/\{(\w+)\}/g)) {
            pattern += escape(value.slice(start, match.index)) + '(.+?)';
            names.push(match[1]);
            start = match.index + match[0].length;
        }
        return {key, names, pattern: new RegExp('^' + pattern + escape(value.slice(start)) + '$')};
    }).sort((a, b) => b.names.length - a.names.length || b.pattern.source.length - a.pattern.source.length);
    function translated(text) {
        const value = text.trim();
        if (exact.has(value)) return text.replace(value, t(exact.get(value)));
        for (const template of templates) {
            const match = value.match(template.pattern);
            if (match) return text.replace(value, t(template.key, Object.fromEntries(template.names.map((name, i) => [name, match[i + 1]]))));
        }
        if (text.includes(' · ')) return text.split(' · ').map(translated).join(' · ');
        if (/[→←]$/.test(value)) {
            const arrow = value.slice(-1);
            return translated(text.slice(0, text.lastIndexOf(arrow))) + arrow;
        }
        if (/^[→←]/.test(value)) {
            const end = text.indexOf(value[0]) + 1;
            return text.slice(0, end) + translated(text.slice(end));
        }
        return text;
    }
    // Vertaal de interface en behoud brongegevens en ingevulde waarden.
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
        if (!node.parentElement.closest('script, style, textarea, pre, code, [data-source-content], #markdown, #toc')) node.textContent = translated(node.textContent);
    }
    for (const element of document.querySelectorAll('[placeholder], [aria-label], [alt], [title]')) {
        if (element.closest('[data-source-content]')) continue;
        for (const attribute of ['placeholder', 'aria-label', 'alt', 'title']) {
            if (element.hasAttribute(attribute)) element.setAttribute(attribute, translated(element.getAttribute(attribute)));
        }
    }
    document.documentElement.lang = language;
    document.title = document.title.split(' · ').map(translated).join(' · ');
    document.querySelectorAll('[data-language]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.language === language)));
    document.dispatchEvent(new CustomEvent('languagechange'));
}

