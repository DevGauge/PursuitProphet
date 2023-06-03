import os
import sys
import uuid
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db = SQLAlchemy()

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

    def __init__(self, user_input, **kwargs):
        super(Goal, self).__init__(**kwargs)
        self.goal = user_input
        self.completed = kwargs.get('completed', False)
    
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
        # Create an engine to connect to your database
        engine = create_engine(DATABASE_URL)

        # Create all tables defined in the models
        Goal.metadata.create_all(engine)

        # Create a session factory
        Session = sessionmaker(bind=engine)

        with flask_app.app_context():
            db.create_all()

        return flask_app
    
app = App().app