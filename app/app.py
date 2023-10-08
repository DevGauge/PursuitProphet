from datetime import datetime
import os
import uuid
import mimetypes
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
from flask import Flask
from flask_migrate import Migrate
from flask_mail import Mail
from dotenv import load_dotenv

from sqlalchemy import create_engine, DateTime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from .pp_logging.db_logger import DBLogger, db
from .pp_logging.event_logger import EventLogger
from flask_security import Security, SQLAlchemyUserDatastore, SQLAlchemyUserDatastore
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField, TimeField
from flask_security.forms import LoginForm, ConfirmRegisterForm
from wtforms.validators import DataRequired, Length, Regexp, Email, Optional

from .models import User, Role

load_dotenv()

class RegistrationForm(ConfirmRegisterForm):
    aka = StringField('Nickname (Optional)', [
        Optional(),
        Length(min=4, max=20),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Nicknames must have only letters, '
               'numbers, dots or underscores')
    ], render_kw={"placeholder": "Enter your preferred name"})
    
class CustomLoginForm(LoginForm):
    email = StringField('Email', [
        DataRequired(),
        Email(message='Invalid email'),
        Length(max=254)
    ])

    password = PasswordField('Password', [
        DataRequired()
    ])

    submit = SubmitField('Login', render_kw={"class": "standard-button"})

class App:
    def __init__(self):
        self.app = self.create_app()

    def create_app(self):
        flask_app = Flask(__name__)
        mail_password=os.getenv('MAIL_PASSWORD')
        flask_app.debug = True
        # flask-security-too
        flask_app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
        print('secret key is None: ', os.getenv('SECRET_KEY') is None)
        flask_app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT')
        print('salt is None: ', os.getenv('SECURITY_PASSWORD_SALT') is None)
        # flask-security-too registration settings
        flask_app.config['SECURITY_REGISTERABLE'] = True
        flask_app.config['SECURITY_CONFIRMABLE'] = True
        flask_app.config['SECURITY_RECOVERABLE'] = True
        flask_app.config['SECURITY_POST_REGISTER_VIEW'] = 'thank_you'
        flask_app.config['SECURITY_INCLUDE_JQUERY'] = True
        flask_app.config['SECURITY_WTFORMS_USE_CDN'] = True
        # mail operations
        flask_app.config['MAIL_SERVER'] = 'smtp.hostinger.com'
        flask_app.config['MAIL_PORT'] = 587
        flask_app.config['MAIL_USE_TLS'] = True
        flask_app.config['MAIL_USERNAME'] = 'no-reply@pursuitprophet.com'
        flask_app.config['MAIL_PASSWORD'] = mail_password
        flask_app.config['MAIL_DEFAULT_SENDER'] = 'no-reply@pursuitprophet.com'
        flask_app.config['SECURITY_TEMPLATE_PATH'] = './app/templates/security/'

        flask_app.mail = Mail(flask_app)
        
        DATABASE_URL = os.getenv("DATABASE_URL")
        if DATABASE_URL is None:
            DATABASE_URL = 'postgresql://kenny:password@localhost:5432/postgres'
        else:
            DATABASE_URL= DATABASE_URL[:8]+'ql' + DATABASE_URL[8:]
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
        flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(flask_app)
        _ = Migrate(flask_app, db)     

        with flask_app.app_context():
            self.user_datastore = SQLAlchemyUserDatastore(db, User, Role)
            # db.drop_all()
            db.create_all()
            db_logger = DBLogger(db)
            self.logger = EventLogger(db_logger)
            flask_app.logger.addHandler(db_logger)
            security = Security(datastore=self.user_datastore,  confirm_register_form=RegistrationForm, login_form=CustomLoginForm)
            security.init_app(flask_app)
            # register_blueprints(flask_app)

        return flask_app

app_instance = App()
app = app_instance.app
