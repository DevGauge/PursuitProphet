import os
from dotenv import load_dotenv
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.models import User
from app.pp_logging.db_logger import db
from shared.blueprints.blueprints import profile_bp
from app.app import RegistrationForm, CustomLoginForm

load_dotenv()

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update user info
        try:
            user = User.query.filter_by(id=current_user.id).first()
        except Exception as e:
            print(f'Error getting user: {e}')
            return redirect(url_for('error_page', error_message='Unknown error. Please try again.'))
        # TDDO: Fix these
        aka = request.form.get('aka')   
        user.aka = aka if aka else user.aka
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile_bp.profile'))
    else:
        # Get user info
        try:
            user = User.query.filter_by(id=current_user.id).first()
        except Exception as e:
            print(f'Error getting user: {e}')
            return redirect(url_for('error_page', error_message='Unknown error. Please try again.'))
        return render_template('profile.html', user=user, aka_form=RegistrationForm(), email_form=CustomLoginForm())
    