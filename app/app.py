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
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, SQLAlchemyUserDatastore
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField, TimeField
from flask_security.forms import LoginForm, ConfirmRegisterForm
from wtforms.validators import DataRequired, Length, Regexp, Email, Optional


load_dotenv()
roles_users = db.Table('roles_users',
    db.Column('user_id', db.String(255), db.ForeignKey('user.id')),
    db.Column('role_id', db.String(255), db.ForeignKey('role.id')))

class DreamForm(FlaskForm):
    goal = StringField('Dream Name', validators=[DataRequired()], render_kw={"placeholder": "What are you dreaming of?"})
    description = TextAreaField('Dream Description', validators=[Optional()], render_kw={"placeholder": "Describe your dream"})
    target_date = DateField('Target Date', format='%Y-%m-%d', validators=[Optional()])
    target_time = TimeField('Target Time', format='%H:%M', validators=[Optional()])
    submit = SubmitField()

    def __init__(self, obj=None, **kwargs):
        super().__init__(obj=obj, **kwargs)

class TaskForm(FlaskForm):
    goal = StringField('Task Name', validators=[DataRequired()], render_kw={"placeholder": "What do you need to do?"})
    target_date = DateField('Target Date', format='%Y-%m-%d', validators=[Optional()])
    target_time = TimeField('Target Time', format='%H:%M', validators=[Optional()])
    submit = SubmitField()

    def __init__(self, obj=None, **kwargs):
        super().__init__(obj=obj, **kwargs)
        if obj:
            self.goal.data = obj.task

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

class Role(db.Model, RoleMixin):
    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    # Example usage
    # admin_role = Role(name='admin')
    # db.session.add(admin_role)
    # user = User(email='admin@admin.com', aka='admin_dude1', password='password')
    # user.roles.append(admin_role)
    # db.session.add(user)
    # db.session.commit()

class Task(db.Model):
    """
    A task is a subtask of a goal.
    Note: Subtasks reuse this class since they follow the same structure and behavior as tasks.
    """    
    id = db.Column(db.String(255),
                   primary_key=True, 
                   default=lambda: str(uuid.uuid4()))
    task: str = db.Column(db.String(255), nullable=False)
    completed: bool = db.Column(db.Boolean, nullable=False)
    parent_id = db.Column(db.String(255), db.ForeignKey('task.id'))
    subtasks = db.relationship('Task', backref=db.backref('parent', remote_side=[id]))
    goal_id = db.Column(db.String(255), db.ForeignKey('goal.id'), nullable=False)
    target_date = db.Column(db.Date, nullable=True)
    target_time = db.Column(db.Time, nullable=True)

    def __init__(self, task: str, goal_id: str, target_date=None, target_time=None, **kwargs):
        super(Task, self).__init__(**kwargs)
        self.task = task
        self.goal_id = goal_id
        self.completed = kwargs.get('completed', False)
        self.target_date = target_date
        self.target_time = target_time

    def mark_as_complete(self):
        """Mark the task as complete."""
        self.completed = True
        self.commit_session()

    def mark_as_incomplete(self):
        """Mark the task as incomplete."""
        self.completed = False
        self.commit_session()

    def is_complete(self) -> bool:
        """Return True if the task is complete, False if it is incomplete."""
        return self.completed
    
    def add_subtask(self, subtask):
        """Add a subtask to the task."""
        self.subtasks.append(subtask)
        self.commit_session()

    def commit_session(self):
        db.session.commit()
        
    def remove_subtask(self, subtask):
        """Remove a subtask from the task."""
        self.subtasks.remove(subtask)        

    def get_subtasks(self) -> list:
        """Return a list of subtasks."""
        return self.subtasks
    
    def get_task(self) -> str:
        """Return the task."""
        return self.task
    
    def _is_child(self):
        """Return True if the task has a parent task, False otherwise."""
        return self.parent_id is not None
    
    def to_dict(self):
        """Convert the task to a dictionary."""
        task_dict = {
            "id": self.id,
            "task": self.task,
            "completed": self.completed,
            "goal_id": self.goal_id
        }
        if not self._is_child():
            task_dict["subtasks"] = [subtask.to_dict(include_subtasks=False) for subtask in self.subtasks]
        return task_dict

class Goal(db.Model):
    id = db.Column(db.String(255),    
                   primary_key=True, 
                   default=lambda: str(uuid.uuid4()))
    goal = db.Column(db.String(255), nullable=False)
    completed: bool = db.Column(db.Boolean, nullable=False)
    tasks = db.relationship('Task', backref='goal', lazy=True, cascade="all, delete")
    user_id = db.Column(db.String(255), db.ForeignKey('user.id'), nullable=True)
    description = db.Column(db.Text, nullable=True)
    target_date = db.Column(db.Date, nullable=True)
    target_time = db.Column(db.Time, nullable=True)
    

    def __init__(self, user_input, description=None, target_date=None, target_time=None, user_id=None, **kwargs):
        super(Goal, self).__init__(**kwargs)
        self.goal = user_input
        self.completed = kwargs.get('completed', False)
        self.user_id = user_id
        self.description = description
        self.target_date = target_date
        self.target_time = target_time
    
    def mark_as_complete(self):
        """Mark the goal as complete."""
        self.completed = True

    def mark_as_incomplete(self):
        """Mark the goal as incomplete."""
        self.completed = False

    def is_complete(self) -> bool:
        """Return True if the goal is complete, False if it is incomplete."""
        return self.completed
    
    def add_task(self, task: Task):
        """Add a task to the goal."""
        self.tasks.append(task)

    def remove_task(self, task: Task):
        """Remove a task from the goal."""
        self.tasks.remove(task)

    def get_tasks(self) -> list:
        """Return a list of tasks."""
        return self.tasks
    
    def get_goal(self) -> str:
        """Return the goal."""
        return self.goal
    
class User(UserMixin, db.Model):
    id = db.Column(db.String(255),
                   primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    fs_uniquifier = db.Column(db.String(255), 
                              unique=True, 
                              nullable=False)
    email = db.Column(db.String(254), 
                      nullable=False, 
                      unique=True)
    aka = db.Column(db.String(20), 
                    nullable=True)
    password = db.Column(db.String(128), 
                         nullable=False)
    roles = db.relationship('Role', 
                            secondary=roles_users, 
                            backref=db.backref('users', lazy='dynamic'))
    aka = db.Column(db.String(20), 
                    nullable=True)
    confirmed_at = db.Column(DateTime)
    goals = db.relationship('Goal', 
                            backref='user', 
                            lazy=True)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    is_temporary = False

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.fs_uniquifier = str(uuid.uuid4())
    
    def set_role(self, role):
        self.roles.append(role)        
    
    def add_goal(self, goal: Goal):
        """Add a goal to the user."""
        self.goals.append(goal)

    def remove_goal(self, goal: Goal):
        """Remove a goal from the user."""
        self.goals.remove(goal)

    def get_goals(self) -> list:
        """Return a list of goals."""
        return self.goals
    
    def get_username(self) -> str:
        """Return the username."""
        return self.aka

class App:
    def __init__(self):
        self.app = self.create_app()

    def create_app(self):
        flask_app = Flask(__name__)
        mail_password=os.getenv('MAIL_PASSWORD')
        flask_app.debug = True
        # flask-security-too
        flask_app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
        flask_app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT')
        # flask-security-too registration settings
        flask_app.config['SECURITY_REGISTERABLE'] = True
        flask_app.config['SECURITY_CONFIRMABLE'] = True        
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

        return flask_app

app_instance = App()
app = app_instance.app
