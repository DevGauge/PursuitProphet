from shared.blueprints.blueprints import google_bp
from flask import url_for, redirect, request
from app.app import oauth

from flask_security.confirmable import confirm_user
from flask_security.utils import hash_password, login_user
from flask_security import login_required, current_user

from app.models import User
from app.pp_logging.db_logger import db

google_client = oauth.create_client('google')

@google_bp.route('/google/login')
def login(referrer: str = None):
    referrer = request.args.get('referrer')
    if referrer == 'profile':
        print('referred from profile')
        redirect_uri = url_for('google_bp.linkUser', _external=True)
    else:
        redirect_uri = url_for('google_bp.authorize', _external=True)

    return google_client.authorize_redirect(redirect_uri)

@google_bp.route('/google/authorize')
def authorize():
    token = google_client.authorize_access_token()
    print(f'token: {token}')
    resp = google_client.get('userinfo')
    print(f'resp: {resp.json()}')

    if not resp.ok:
        return redirect(url_for('error_page', error_message='Bad Response from Google'))

    user_info = resp.json()
    email = user_info['email']
    confirmed = user_info['verified_email']
    google_id = user_info['id']

    try:
        user = User.query.filter_by(email=email).first()
        print(f'user: {user}')
    except Exception as e:
        print(f'Error finding user: {e}')
        return redirect(url_for('error_page', error_message='Error finding user'))

    # Create a new user if one doesn't exist
    if user is None:
        print('Creating new user')
        user = User(email=email, password=hash_password('password123!'), active=True, google_id=google_id)
        db.session.add(user)
        db.session.commit()

    if confirmed and not user.confirmed_at:
        print('Confirming user')
        confirm_user(user)
        db.session.commit()

    if not user.active:
        print('Activating user')
        user.active = True
        db.session.commit()

    if not user.google_id:
        return redirect(url_for('error_page', error_message='Google account not linked to email account. Please login with email and password, then visit your profile and link your google account.'))
    
    if not confirmed:
        return redirect(url_for('error_page', error_message='Google account not verified. Please verify your google account and try again.'))

    print('Logging in user')
    login_user(user)    
    linkUserPrimaryGoogleEmail(email)
    return redirect(url_for('dashboard'))

@login_required
@google_bp.route('/google/link_user')
def linkUser():
    print("linking user")
    token = google_client.authorize_access_token()
    resp = google_client.get('userinfo')

    if not resp.ok:
        return redirect(url_for('error_page', error_message='Bad Response from Google'))

    user_info = resp.json()
    confirmed = user_info['verified_email']
    google_id = user_info['id']

    # Confirm user if their Google account is verified and they are not confirmed yet
    if not confirmed:
        return redirect(url_for('error_page', error_message='Google account not verified. Please verify your google account with Google and try again.'))

    try:
        curr_user = current_user._get_current_object()
        curr_user.google_id = google_id
        db.session.commit()
    except Exception as e:
        print(f'Error linking user: {e}')
        return redirect(url_for('error_page', error_message='Unknown error. Please try again.'))
    linkUserPrimaryGoogleEmail(user_info['email'])
    return redirect(url_for('profile_bp.profile'))

def linkUserPrimaryGoogleEmail(email: str):
    try:
        curr_user = current_user._get_current_object()
        curr_user.primary_google_email = email
        db.session.commit()
    except Exception as e:
        print(f'Error linking user: {e}')
        return redirect(url_for('error_page', error_message='Unknown error. Please try again.'))
