import os
from flask import Blueprint, url_for

# Google Oauth
from authlib.integrations.flask_client import OAuth
# TODO use blueprint instead of app
from app.app import app
from dotenv import load_dotenv
load_dotenv()

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'email profile'},
)

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize', _external=True)
    print(f"redirecting to {redirect_uri}")
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    if resp.ok:
        user_info = resp.json()
        print(user_info)
        email = user_info['email']
        return f'You are {email} on Google'
    return 'Bad Resp'

def construct_blueprint(name: str):
    """Constructs a blueprint with the given name and template_folder, which defaults to the name"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.abspath(os.path.join(current_dir, '../../features'))
    template_path = os.path.join(root_path, name, 'templates')
    static_path = os.path.join(root_path, name, 'static')
    
    return Blueprint(name + '_bp', __name__, template_folder=template_path, static_folder=static_path, static_url_path=f'/{name}_static')

demo_bp = construct_blueprint('demo')
dream_bp = construct_blueprint('dream')
task_bp = construct_blueprint('task')
subtask_bp = construct_blueprint('subtask')

def register_blueprints(flask_app):
    blueprints = [demo_bp, dream_bp, task_bp, subtask_bp]
    for blueprint in blueprints:
        flask_app.register_blueprint(blueprint)
        print(f'registered blueprint: {blueprint.name} with url_prefix: {blueprint.url_prefix}, template_folder: {blueprint.template_folder}, static_folder: {blueprint.static_folder}')
