const target = document.querySelector('#markdown');
const toc = document.querySelector('#toc');

const escapeHtml = value => value.replace(
    /[&<>"']/g,
    character => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    })[character]
);

const slugify = value => value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');

function inline(value) {
    return value
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
}

function markdown(markdownText) {
    const lines = escapeHtml(markdownText)
        .replace(/\r/g, '')
        .split('\n');
    const output = [];
    let paragraph = [];
    let list = null;
    let code = false;
    let codeLanguage = '';
    let codeLines = [];
    let tableLines = [];

    const flushParagraph = () => {
        if (paragraph.length) {
            output.push(`<p>${inline(paragraph.join(' '))}</p>`);
            paragraph = [];
        }
    };

    const closeList = () => {
        if (list) {
            output.push(`</${list}>`);
            list = null;
        }
    };

    const flushTable = () => {
        if (!tableLines.length) {
            return;
        }

        const rows = tableLines.map(line => line
            .replace(/^\s*\||\|\s*$/g, '')
            .split('|')
            .map(cell => cell.trim()));
        const divider = rows[1] && rows[1].every(
            cell => /^:?-{3,}:?$/.test(cell)
        );

        if (divider) {
            const header = rows[0]
                .map(cell => `<th>${inline(cell)}</th>`)
                .join('');
            const body = rows.slice(2)
                .map(row => `<tr>${row
                    .map(cell => `<td>${inline(cell)}</td>`)
                    .join('')}</tr>`)
                .join('');
            output.push(`
                <div class="table-wrap">
                    <table>
                        <thead><tr>${header}</tr></thead>
                        <tbody>${body}</tbody>
                    </table>
                </div>
            `);
        } else {
            output.push(`<p>${inline(tableLines.join(' '))}</p>`);
        }
        tableLines = [];
    };

    for (const line of lines) {
        if (line.startsWith('```')) {
            flushParagraph();
            closeList();

            if (code) {
                if (codeLanguage === 'mermaid') {
                    output.push(`
                        <div class="diagram mermaid">
                            ${codeLines.join('\n')}
                        </div>
                    `);
                } else {
                    output.push(`<pre><code>${codeLines.join('\n')}</code></pre>`);
                }

                codeLines = [];
                codeLanguage = '';
            } else {
                codeLanguage = line.slice(3).trim().toLowerCase();
            }

            code = !code;
            continue;
        }

        if (code) {
            codeLines.push(line);
            continue;
        }

        if (/^\s*\|.*\|\s*$/.test(line)) {
            flushParagraph();
            closeList();
            tableLines.push(line);
            continue;
        }

        flushTable();

        const heading = line.match(/^(#{1,4})\s+(.+)$/);

        if (heading) {
            flushParagraph();
            closeList();

            const level = heading[1].length;
            const id = slugify(heading[2]);

            output.push(
                `<h${level} id="${id}">${inline(heading[2])}</h${level}>`
            );
            continue;
        }

        const unorderedListItem = line.match(/^\s*[-*]\s+(.+)$/);
        const orderedListItem = line.match(/^\s*\d+\.\s+(.+)$/);

        if (unorderedListItem || orderedListItem) {
            flushParagraph();

            const kind = unorderedListItem ? 'ul' : 'ol';

            if (list !== kind) {
                closeList();
                output.push(`<${kind}>`);
                list = kind;
            }

            const listItem = unorderedListItem || orderedListItem;
            output.push(`<li>${inline(listItem[1])}</li>`);
            continue;
        }

        if (/^>\s?/.test(line)) {
            flushParagraph();
            closeList();

            const quote = inline(line.replace(/^>\s?/, ''));
            output.push(`<blockquote><p>${quote}</p></blockquote>`);
            continue;
        }

        if (!line.trim()) {
            flushParagraph();
            closeList();
            continue;
        }

        paragraph.push(line.trim());
    }

    flushParagraph();
    closeList();
    flushTable();

    if (codeLines.length) {
        output.push(`<pre><code>${codeLines.join('\n')}</code></pre>`);
    }

    return output.join('\n');
}

async function renderMermaidDiagrams() {
    const diagrams = [...target.querySelectorAll('.mermaid')];

    if (!diagrams.length) {
        return;
    }

    try {
        const {default: mermaid} = await import(
            'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs'
        );

        mermaid.initialize({
            startOnLoad: false,
            securityLevel: 'strict',
            theme: 'base',
            themeVariables: {
                primaryColor: '#fde9eb',
                primaryTextColor: '#231b1b',
                primaryBorderColor: '#ec0000',
                lineColor: '#ec0000',
                secondaryColor: '#f8c7d0',
                tertiaryColor: '#ffffff',
                fontFamily: 'Inter, Arial, Helvetica, sans-serif'
            },
            flowchart: {
                htmlLabels: true,
                useMaxWidth: true,
                curve: 'basis'
            }
        });

        await mermaid.run({
            nodes: diagrams,
            suppressErrors: true
        });
    } catch (error) {
        diagrams.forEach(diagram => {
            if (!diagram.querySelector('svg')) {
                const source = diagram.textContent.trim();

                diagram.className = 'diagram diagram-fallback';
                diagram.innerHTML = `<pre><code>${escapeHtml(source)}</code></pre>`;
            }
        });
    }
}

function buildTableOfContents() {
    const headings = [...target.querySelectorAll('h2,h3')];

    toc.innerHTML = headings
        .map(heading => {
            const className = heading.tagName === 'H3' ? 'sub' : '';
            return `
                <a class="${className}" href="#${heading.id}">
                    ${heading.textContent}
                </a>
            `;
        })
        .join('');

    const links = [...toc.querySelectorAll('a')];
    const observer = new IntersectionObserver(
        entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    links.forEach(link => {
                        link.classList.toggle(
                            'active',
                            link.hash === '#' + entry.target.id
                        );
                    });
                }
            });
        },
        {
            root: document.querySelector('.manual-content'),
            rootMargin: '-70px 0px -70% 0px'
        }
    );

    headings.forEach(heading => observer.observe(heading));
}

async function load() {
    try {
        const response = await fetch('/api/werkinstructie', {
            cache: 'no-store'
        });

        if (!response.ok) {
            throw Error('De werkinstructie kon niet worden opgehaald.');
        }

        const markdownText = await response.text();

        target.innerHTML = markdown(markdownText);
        await renderMermaidDiagrams();
        document.querySelector('#readTime').textContent =
            `± ${Math.max(1, Math.ceil(markdownText.split(/\s+/).length / 220))} ` +
            'min. leestijd';
        buildTableOfContents();
    } catch (error) {
        target.innerHTML = `
            <div class="manual-error">
                <strong>Laden mislukt</strong>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;
        toc.innerHTML = '<span class="loading-line">Niet beschikbaar</span>';
    }
}

document.querySelector('#print').onclick = () => window.print();

load();
