import os
from dotenv import load_dotenv
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.models import User
from app.pp_logging.db_logger import db
from shared.blueprints.blueprints import profile_bp


load_dotenv()

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update user info
        user = User.query.filter_by(id=current_user.id).first()
        user.email = request.form['email'] if request.form['email'] else user.email
        user.first_name = request.form['first_name'] if request.form['first_name'] else user.first_name
        user.last_name = request.form['last_name'] if request.form['last_name'] else user.last_name
        user.phone_number = request.form['phone_number'] if request.form['phone_number'] else user.phone_number
        user.address = request.form['address'] if request.form['address'] else user.address
        user.city = request.form['city'] if request.form['city'] else user.city
        user.state = request.form['state'] if request.form['state'] else user.state
        user.zip_code = request.form['zip_code'] if request.form['zip_code'] else user.zip_code
        user.country = request.form['country'] if request.form['country'] else user.country
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile_bp.profile'))
    else:
        # Get user info
        user = User.query.filter_by(id=current_user.id).first()
        return render_template('profile.html', user=user)