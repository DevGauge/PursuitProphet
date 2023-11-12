import os
from shared.blueprints.blueprints import google_bp
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import url_for
from app.app import app
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

@google_bp.route('/google/login')
def login():
    redirect_uri = url_for('google_bp.authorize', _external=True)
    print(f"redirecting to {redirect_uri}")
    return google.authorize_redirect(redirect_uri)

@google_bp.route('/google/authorize')
def authorize():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    if resp.ok:
        user_info = resp.json()
        print(user_info)
        email = user_info['email']
        return f'You are {email} on Google'
    return 'Bad Resp'
