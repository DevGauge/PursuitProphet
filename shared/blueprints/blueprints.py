import json
import os
from flask import Blueprint
from flask_dance.contrib.google import google, make_google_blueprint
from google.oauth2 import id_token
from app.models import User
from app.pp_logging.db_logger import db
from flask import flash, request
from flask_login import login_user
from flask import redirect, url_for, session, Response

from dotenv import load_dotenv
load_dotenv()

def construct_blueprint(name: str):
    """Constructs a blueprint with the given name. The blueprint's template and static folders are located in the features/<name>/template or /static folder."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.abspath(os.path.join(current_dir, '../../features'))
    template_path = os.path.join(root_path, name, 'templates')
    static_path = os.path.join(root_path, name, 'static')
    
    return Blueprint(name + '_bp', __name__, template_folder=template_path, static_folder=static_path, static_url_path=f'/{name}_static')

demo_bp = construct_blueprint('demo')
dream_bp = construct_blueprint('dream')
task_bp = construct_blueprint('task')
subtask_bp = construct_blueprint('subtask')

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=["profile", "email"]
)

def register_blueprints(flask_app):
    blueprints = [demo_bp, dream_bp, task_bp, subtask_bp]
    for blueprint in blueprints:
        flask_app.register_blueprint(blueprint)
        print(f'registered blueprint: {blueprint.name} with url_prefix: {blueprint.url_prefix}, template_folder: {blueprint.template_folder}, static_folder: {blueprint.static_folder}')
        
    flask_app.register_blueprint(google_bp, url_prefix='/google_login')
    

def get_user_info(): 
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    resp = google.get("https://people.googleapis.com/v1/people/me?key=" + GOOGLE_API_KEY + "&personFields=names,emailAddresses")
    if not google.authorized:
        print('Google not authorized')
        return redirect(url_for("google.login"))
    print(resp)
    if resp.status_code == 200:
        print('GoOGLE StaTUS CODE 200')
        return resp.json()
    else:
        raise Exception(f"Failed to fetch user info from Google: {resp.status_code}")

def login_user_with_google():
    """Logs the user in using their Google account."""
    user_info = get_user_info()
    # if user_info is redirect, there was an auth error
    if isinstance(user_info, Response):
        return user_info
    
    email_addresses = user_info.get('emailAddresses', [])
    email = email_addresses[0].get('value') if email_addresses else None

    user = User.query.filter_by(email=email).first()
    if user is not None:
        login_user(user)
    else:
        # Create a new user account.
        user = User(email=email)
        db.session.add(user)
        db.session.commit()

        # Log the user in.
        login_user(user)

    return redirect(url_for('dashboard'))

@google_bp.route("/login", endpoint='google_bp_login')
def login():
    print('google_bp_login')
    GOOGLE_CALLBACK_URI = os.getenv('GOOGLE_CALLBACK_URI')
    # Redirect the user to the Google OAuth login page.
    return google.authorize(callback_uri=GOOGLE_CALLBACK_URI)

@google_bp.route('/callback', methods=['GET', 'POST'])
def callback():
    oauth_resp = get_user_info()

    # Log the user in using their Google account.
    login_user_with_google()

    flash("Successfully authenticated.", category="success")
    return redirect(url_for('dashboard'))

@google_bp.route("/logout", endpoint='google_bp_logout')
def logout():
    session.clear()
    return redirect(url_for("dashboard"))
