export function bindSecretToggles() {
    document.querySelectorAll('.secret-toggle').forEach(button => {
        const input = document.getElementById(button.getAttribute('aria-controls'));
        button.onclick = () => {
            const visible = input.type === 'password';
            input.type = visible ? 'text' : 'password';
            button.setAttribute('aria-pressed', String(visible));
        };
        button.disabled = false;
    });
}
