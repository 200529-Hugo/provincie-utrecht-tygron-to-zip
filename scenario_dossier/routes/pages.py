from flask import Blueprint, current_app, g, redirect, render_template, request, send_from_directory

pages = Blueprint('pages', __name__)


@pages.get('/')
@pages.get('/login')
def login_page():
    if g.account:
        return redirect('/projecten')
    return render_template('login.html')


@pages.get('/projecten')
def projects_page():
    demo_mode = request.args.get('mode') == 'demo'
    if not g.account and not demo_mode:
        return redirect('/login')
    return render_template('projects.html', demo_mode=demo_mode)


@pages.get('/login-key')
def login_key_page():
    return render_template('login-key.html', current_step=2, workflow_mode='legacy', login_key_mode=True)


@pages.get('/workflow')
@pages.get('/index.html')
def workflow_page():
    mode = request.args.get('mode')
    if mode not in ('account', 'demo', 'tygron', 'legacy'):
        return redirect('/projecten' if g.account else '/login')
    if mode == 'legacy':
        return login_key_page()
    if mode == 'account' and not g.account:
        return redirect('/login')
    if mode == 'demo' and not request.args.get('project_id'):
        return redirect('/projecten?mode=demo')
    current_step = 3 if mode in ('account', 'demo') else 2
    template = 'active-session.html' if mode == 'tygron' else 'index-new.html'
    return render_template(template, current_step=current_step, workflow_mode=mode, demo_mode=mode == 'demo',
                           active_session_mode=mode == 'tygron')


@pages.get('/controle')
@pages.get('/controle/')
@pages.get('/controle.html')
def control_page():
    return render_template('controle-new.html')


@pages.get('/werkinstructie')
@pages.get('/werkinstructie/')
@pages.get('/werkinstructie.html')
def manual_page():
    return render_template('werkinstructie-new.html')


@pages.get('/<path:filename>')
def legacy_static(filename):
    return send_from_directory(current_app.static_folder, filename)
