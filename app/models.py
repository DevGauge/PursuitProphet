from .pp_logging.db_logger import db
from flask_security import UserMixin, RoleMixin
import uuid
from sqlalchemy import DateTime

# TODO: Separate logic from models
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
from flask import session


roles_users = db.Table('roles_users',
    db.Column('user_id', db.String(255), db.ForeignKey('user.id')),
    db.Column('role_id', db.String(255), db.ForeignKey('role.id')))

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
    
    def get_goal(self) -> str:
        """Return the goal."""
        parent = Goal.query.filter_by(id=self.goal_id).first()
        return parent.goal

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
    # region tutorial
    is_first_login = db.Column(db.Boolean(), default=True)
    is_first_detail_view = db.Column(db.Boolean(), default=True)
    is_first_new_goal = db.Column(db.Boolean(), default=True)
    is_first_new_task = db.Column(db.Boolean(), default=True)
    is_first_new_subtask = db.Column(db.Boolean(), default=True)
    
    # region demo
    is_temporary = False # true for demo user, used as holding for goal
    is_first_demo_task_gen = db.Column(db.Boolean(), default=True)
    is_first_demo_subtask_gen = db.Column(db.Boolean(), default=True)
    is_demo_finished = db.Column(db.Boolean(), default=False)
    # endregion demo
    # endregion tutorial

    # region google_oauth
    google_id = db.Column(db.String(255), nullable=True)
    # endregion google_oauth

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.fs_uniquifier = str(uuid.uuid4())

    def is_google_user(self):
        return self.google_id is not None
    
    def set_role(self, role):
        self.roles.append(role)        
    
    def add_goal(self, goal: Goal):
        """Add a goal to the user."""
        self.goals.append(goal)
    
    def does_user_have_goal(self):
        return len(self.goals) > 0

    def remove_goal(self, goal: Goal):
        """Remove a goal from the user."""
        self.goals.remove(goal)

    def get_goals(self) -> list:
        """Return a list of goals."""
        return self.goals
    
    def get_username(self) -> str:
        """Return the username."""
        return self.aka

class ChatBot:
    def __init__(self, goal_manager, goal_generator_bot, api_key=None):
        self.io_manager = goal_manager.io_manager
        if api_key is None:
            api_key = self.io_manager.get_open_ai_key()
        self.goal_manager = goal_manager
        self.goal_gen_bot = goal_generator_bot
    
    def run(self):
        """Main function"""
        print()
        self.display_welcome_message()
        self.set_assistant_primary_goal()
        self.goal_gen_bot.goal = self.io_manager.primary_goal.get_goal()
        suggested_goals = self.goal_gen_bot.generate_goals()        
        self.goal_manager.goals = self.goal_manager.strip_goals_and_save(suggested_goals)
        self.io_manager.ask_user_to_review_goals(self.goal_manager.goals)
        user_choice = self.io_manager.get_user_choice(['keep', 'modify', 'new'])
        if user_choice == 'modify' or user_choice == 'new':
            pass #TODO: implement modify and new using langchain
        for n in range(len(self.goal_manager.goals)):
            self.goal_manager.generate_subtasks(n)
            # self.goal_manager.handle_user_task_interaction()
        self.goal_manager.save_goals_to_disk_in_json()

    def set_primary_goal(self, user_input, user = None):
        if user:
            primary_goal = Goal(user_input, user)
            print('set primary goal: ', primary_goal.goal, 'for user: ', user)
        else:
            print('creating temp user')
            temp_user = User(email=str(uuid.uuid4()) + "@temp.com",  # Use a dummy email for the temporary user
                                       password=generate_password_hash("temp_password"),  # Use a dummy password for the temporary user
                                       is_temporary=True)
            db.session.add(temp_user)
            db.session.commit()
            primary_goal = Goal(user_input, user_id=temp_user.id)
            
        try:
            db.session.add(primary_goal)
            db.session.commit()
            session['temp_user_id'] = temp_user.id
            return primary_goal.id

        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    def display_welcome_message(self):
        """Display the welcome message"""        
        welcome_message = "Hi! I'm Pursuit Prophet, brought to you by DevGauge."
        self.io_manager.assistant_message(welcome_message)

    def set_assistant_primary_goal(self, primary_goal=None):
        """Set the assistant role based on user input"""
        if primary_goal is None:
            self.set_primary_goal(self.io_manager.get_user_input("What are you dreaming of today?"))
        else:
            goal_id = self.set_primary_goal(primary_goal)
            return goal_id
        # print(f'{self.io_manager.primary_goal.goal} was set')
        
    
    def generate_goals(self, primary_goal, num_goals=10):
        """Generate goals using the OpenAI API"""
        print(f'generating goals for {primary_goal.get_goal()}')
        self.goal_gen_bot.goal = primary_goal.get_goal()
        self.goal_gen_bot.num_goals = num_goals
        #strip and save
        try:
            self.goal_manager.strip_tasks_and_save(self.goal_gen_bot.generate_goals(), primary_goal.id)
        except Exception as e:
            # go to error route
            raise e

    def generate_subtasks(self, task: Task, num_tasks=10):
        """Generate subtasks for a given goal"""
        return self.goal_manager.generate_subtasks(task, num_tasks)
