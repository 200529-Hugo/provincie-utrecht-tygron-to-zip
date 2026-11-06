import {t} from './i18n.js';
import {loginAccount} from './api/auth.js';
import {bindSecretToggles} from './secret-toggle.js';

const form = document.querySelector('#loginForm');
if (form) {
    const password = document.querySelector('#loginPassword');
    bindSecretToggles();
    form.onsubmit = async event => {
        event.preventDefault();
        const button = document.querySelector('#loginButton');
        const error = document.querySelector('#loginError');
        button.disabled = true;
        button.firstElementChild.textContent = t('Inloggen…');
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
            button.firstElementChild.textContent = t('Inloggen');
            form.setAttribute('aria-busy', 'false');
        }
    };
}
