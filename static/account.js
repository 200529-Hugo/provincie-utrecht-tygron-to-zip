import {t} from './i18n.js';
import {loginAccount} from './api/auth.js';

const form = document.querySelector('#loginForm');
if (form) {
    const password = document.querySelector('#loginPassword');
    document.querySelector('#showPassword').onclick = event => {
        const visible = password.type === 'password';
        password.type = visible ? 'text' : 'password';
        event.currentTarget.setAttribute('aria-pressed', String(visible));
        event.currentTarget.textContent = t(visible ? 'Verbergen' : 'Tonen');
    };
    form.onsubmit = async event => {
        event.preventDefault();
        const button = document.querySelector('#loginButton');
        const error = document.querySelector('#loginError');
        button.disabled = true;
        button.textContent = t('Inloggen…');
        error.textContent = '';
        form.setAttribute('aria-busy', 'true');
        try {
            await loginAccount({
                username: document.querySelector('#loginUsername').value.trim(), password: password.value,
                base_url: document.querySelector('#loginBaseUrl').value.trim(), domain: document.querySelector('#loginDomain').value.trim()
            });
            sessionStorage.removeItem('selectedProject');
            location.assign('/projecten');
        } catch (failure) {
            error.textContent = failure.message;
            password.focus();
        } finally {
            password.value = '';
            button.disabled = false;
            button.textContent = t('Inloggen');
            form.setAttribute('aria-busy', 'false');
        }
    };
}
