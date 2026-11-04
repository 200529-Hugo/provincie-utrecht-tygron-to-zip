import {changeLanguage} from './i18n.js';
import {logoutAccount} from './api/auth.js';
import {getTranslations} from './api/settings.js';

// De taalcookie wordt gedeeld door alle pagina’s en bevat geen accountgegevens.
document.querySelectorAll('[data-language]').forEach(button => {
    button.addEventListener('click', async () => {
        const buttons = document.querySelectorAll('[data-language]');
        buttons.forEach(item => { item.disabled = true; });
        try {
            const next = button.dataset.language;
            const data = await getTranslations({language: next});
            document.cookie = `language=${next}; Path=/; Max-Age=31536000; SameSite=Lax${location.protocol === 'https:' ? '; Secure' : ''}`;
            changeLanguage(next, data);
        } catch (error) { alert(error.message); }
        finally { buttons.forEach(item => { item.disabled = false; }); }
    });
});
document.querySelector('#logout')?.addEventListener('click', async event => {
    event.currentTarget.disabled = true;
    try {
        await logoutAccount();
        sessionStorage.removeItem('selectedProject');
        location.assign('/login');
    } catch (error) {
        event.currentTarget.disabled = false;
        alert(error.message);
    }
});

// Wissel lokale workflowstappen zonder de ingevulde waarden te verliezen.
document.addEventListener('click', event => {
    const button = event.target.closest('button[data-step-href]');
    if (button && !button.disabled && !event.defaultPrevented) location.assign(button.dataset.stepHref);
});
