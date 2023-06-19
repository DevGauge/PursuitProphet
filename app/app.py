from datetime import datetime
import os
import uuid
from flask import Flask
from flask_migrate import Migrate

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .pp_logging.db_logger import DBLogger, db
from .pp_logging.event_logger import EventLogger
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, Regexp, Email

roles_users = db.Table('roles_users',
    db.Column('user_id', db.String(255), db.ForeignKey('user.id')),
    db.Column('role_id', db.String(255), db.ForeignKey('role.id')))

class RegistrationForm(FlaskForm):
    email = StringField('Email', [
        DataRequired(),
        Email(message='Invalid email'),
        Length(max=254)
    ])

    password = PasswordField('Password', [
        DataRequired(),
        Length(min=12, max=64),
        Regexp('^(?=.*[A-Z])(?=.*[!@#$&*])(?=.*[0-9])(?=.*[a-z]).*$',
               message="Password must have at least one lowercase letter, one uppercase letter, one number, and one special character")
    ])

    username = StringField('Nickname (Optional)', [
        Length(min=4, max=20),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Nicknames must have only letters, '
               'numbers, dots or underscores')
    ])

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

    def __init__(self, task: str, goal_id: str, parent_id: str = None, **kwargs):
        super(Task, self).__init__(**kwargs)
        self.task = task
        self.goal_id = goal_id
        self.parent_id = parent_id
        self.completed = kwargs.get('completed', False)

    def mark_as_complete(self):
        """Mark the task as complete."""
        self.completed = True
        db.session.commit()

    def mark_as_incomplete(self):
        """Mark the task as incomplete."""
        self.completed = False
        db.session.commit()

    def is_complete(self) -> bool:
        """Return True if the task is complete, False if it is incomplete."""
        return self.completed
    
    def add_subtask(self, subtask):
        """Add a subtask to the task."""
        self.subtasks.append(subtask)
        db.session.commit()

    def remove_subtask(self, subtask):
        """Remove a subtask from the task."""
        self.subtasks.remove(subtask)
        db.session.commit()

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
    tasks = db.relationship('Task', backref='goal', lazy=True)
    user_id = db.Column(db.String(255), db.ForeignKey('user.id'), nullable=True)

    def __init__(self, user_input, user_id=None, **kwargs):
        super(Goal, self).__init__(**kwargs)
        self.goal = user_input
        self.completed = kwargs.get('completed', False)
        self.user_id = user_id
    
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
    
class User(db.Model):
    id = db.Column(db.String(255),
                   primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(254), nullable=False, unique=True)
    password = db.Column(db.String(64), nullable=False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    aka = db.Column(db.String(20), nullable=True)
    goals = db.relationship('Goal', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def set_role(self, role):
        self.roles.append(role)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
    
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
        return self.username

class App:
    def __init__(self):
        self.app = self.create_app()

    def create_app(self):
        flask_app = Flask(__name__)
        DATABASE_URL = os.getenv("DATABASE_URL")
        if DATABASE_URL is None:
            DATABASE_URL = 'postgresql://kenny:password@localhost:5432/postgres'
        else:
            DATABASE_URL= DATABASE_URL[:8]+'ql' + DATABASE_URL[8:]
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
        flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(flask_app)
        _ = Migrate(flask_app, db)
        # Create an engine to connect to your database
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)

        # Create all tables defined in the models
        Goal.metadata.create_all(engine)

        # Create a session factory
        Session = sessionmaker(bind=engine)        

        with flask_app.app_context():
            db.create_all()
            db_logger = DBLogger(db)
            self.logger = EventLogger(db_logger)
            flask_app.logger.addHandler(db_logger)

        return flask_app

app_instance = App()
app = app_instance.app