import os
import sys
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, after_this_request
from flask_restx import Api, Resource, fields
sys.path.insert(0, '../')
sys.path.insert(0, '/app')
from bot import ChatBot
from langchain_m.langchain_module import TaskChatBot, GoalChatBot
import app.app
from app.app import Goal, Task, User
from app.app import DreamForm, TaskForm
from app.app import db, app_instance
from flask_socketio import SocketIO, send, emit
from flask_security import roles_required, login_required, login_user, user_registered, current_user
from flask_security.confirmable import confirm_user, confirm_email_token_status
from LangChainAgentFactory import AgentFactory
from langchain.tools import StructuredTool
import traceback
from urllib.parse import quote

app = app_instance.app
app.debug_mode = True
socketio = SocketIO(app)

bot = ChatBot()

@user_registered.connect_via(app)
def user_registered_sighandler(sender, user, confirm_token, confirmation_token, form_data):
    @after_this_request
    def transfer_goals_after_request(response):
        if 'temp_user_id' in session:
            temp_user_id = session['temp_user_id']
            temp_user = User.query.get(temp_user_id)
            if temp_user is not None:
                # Transfer the goals from the temporary user to the registered user
                for goal in temp_user.goals:
                    user.goals.append(goal)
            
                # Ensure that goals are persisted in the database before deleting temp_user
                db.session.flush()

                # Delete the temporary user
                db.session.delete(temp_user)
                db.session.commit()
        return response

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)
    send(data, broadcast=True)

from sqlalchemy import exc
@app.errorhandler(exc.SQLAlchemyError)
def handle_db_exceptions(error):
    db.session.rollback()

@app.route('/error/<string:error_message>')
def error_page(error_message):
    print(f'error message: {error_message}')
    # traceback.print_exc()
    return render_template('error.html', error_message=error_message)

@app.errorhandler(500)
def handle_500(error):
    error_message = "Internal Server Error"
    return redirect(url_for('error_page', error_message=error_message))

@app.route('/demo', methods=['GET', 'POST'])
def role_selection():
    if request.method == 'POST':
        role = request.form.get('role')
        goal_id = bot.set_assistant_primary_goal(role)
        return redirect(url_for('demo_goal_generation', num_goals=10, title=role, goal_id=goal_id))
    else:
        roles = ['Write a blog post about cats', 'Organize my house', 'Learn about quantum physics']
        return render_template('role_selection.html', roles=roles)

@app.route('/admin')
@login_required
@roles_required('admin')
def admin_home():
    return "Hello, Admin!"

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/confirm/<token>')
def confirm_email(token):
    # Check the token status first
    expired, invalid, user = confirm_email_token_status(token)
    
    if not expired and not invalid:
        # confirm the user
        if confirm_user(token):
            # if successful, log the user in
            login_user(user)
            return redirect(url_for('dashboard'))
    return 'The confirmation link is invalid or has expired.'

@app.route('/feature/<feature_key>', methods=['GET'])
def get_user_feature(feature_key):
    user_id = request.args.get('user_id', None)
    if user_id is None:
        user = current_user
    else:
        user = User.query.get(user_id)

    feature_value = getattr(user, feature_key, None)
    if feature_value is not None:
        print(f'feature key value: {feature_value}')
        return jsonify({feature_key: feature_value})
    else:
        print(f'feature key {feature_key} not found. user attribs: {user.__dict__}')
        return jsonify({feature_key: False})
    
@app.route('/feature/<feature_key>', methods=['PUT'])
def update_feature_value(feature_key):
    user_id = request.args.get('user_id', None)
    print(f'user id from request: {user_id}')
    if user_id is None:
        user = current_user
    else:
        user = User.query.get(user_id)
    if hasattr(user, feature_key):
            print(f'feature value: {feature_key} found, setting false')
            setattr(user, feature_key, False)
            db.session.commit()
            return jsonify({'success': True})
    else:
        print(f'feature value {feature_key} not found. user attribs: {user.__dict__}')
        app.logger.error(f'feature value {feature_key} not found. user attribs: {user.__dict__}')
        return jsonify({'success': False})

@login_required
@app.route('/')
def dashboard():    
    try:        
        if current_user.is_authenticated:
            user_id = current_user.id
            user = app_instance.user_datastore.find_user(id=user_id)
            if user is not None:
                goals = Goal.query.filter_by(user_id=user_id).all()
                return render_template('dream-home.html', goals=goals)
        else:
            raise ValueError("User not found")
    except Exception as e:
        return redirect(url_for('security.login'))
    
    return redirect(url_for('security.login'))

@app.route('/delete_goal/<goal_id>', methods=['GET', 'POST'])
def delete_goal(goal_id):
    goal=Goal.query.filter_by(id=goal_id).first()
    if goal is None:
        flash('Goal not found.', 'error')
        return redirect(url_for('dashboard'))
    else:
        db.session.delete(goal)
        db.session.commit()
        flash('Your dream has been deleted.', 'success')
        return redirect(url_for('dashboard'))
    
@app.route('/delete_task/<task_id>', methods=['GET', 'POST'])
def delete_task(task_id):
    task=Task.query.filter_by(id=task_id).first()
    print(f'task parent id: {task.goal_id}')
    goal = Goal.query.filter_by(id=task.goal_id).first()
    if task is None:
        flash('Task not found.', 'error')
        print("task not found")
        return redirect(url_for('dashboard'))
    else:
        db.session.delete(task)
        db.session.commit()
        flash('Your task has been deleted.', 'success')    
    if goal is not None:
        print(f"goal and task found: {goal.goal}\n{task.task}")
        return redirect(url_for('view_tasks', goal_id=goal.id, title=goal.goal, subtitle=None))
    else:
        print(f'goal with id {task.goal_id} not found')
        return redirect(url_for('dashboard'))
    
@app.route('/delete_subtask/<subtask_id>', methods=['GET', 'POST'])
def delete_subtask(subtask_id):
    subtask=Task.query.filter_by(id=subtask_id).first()
    print(f'subtask parent id: {subtask.parent_id}')
    task = Task.query.filter_by(id=subtask.parent_id).first()
    goal = Goal.query.filter_by(id=task.goal_id).first()
    if subtask is None:
        flash('Subtask not found.', 'error')
        print("subtask not found")
        return redirect(url_for('dashboard'))
    else:
        db.session.delete(subtask)
        db.session.commit()
        flash('Your task has been deleted.', 'success')
    if task is not None:
        print(f"task and subtask found: {task.task}\n{subtask.task}")
        return redirect(url_for('view_subtasks', task_id=task.id, title=goal.goal))
    else:
        print(f'goal with id {task.goal_id} not found')
        return redirect(url_for('dashboard'))

@app.route('/add_dream', methods=['GET', 'POST'])
def add_dream():
    form = DreamForm()
    form.submit.label.text = 'Add Dream'
    if form.validate_on_submit():
        new_goal = Goal(form.goal.data, 
                        user_id=current_user.id, 
                        description=form.description.data,
                        target_date=form.target_date.data, 
                        target_time=form.target_time.data)
        db.session.add(new_goal)
        db.session.commit()
        flash('Your dream has been added.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('goal-detail.html', form=form, goal=None)

@app.route('/new_task/<goal_id>', methods=['GET', 'POST'])
def new_task(goal_id: str):
    form = TaskForm()
    form.submit.label.text = 'Add Task'
    goal = Goal.query.filter_by(id=goal_id).first()
    if form.validate_on_submit():
        new_task = Task(form.goal.data,
                        goal_id=goal_id,
                        target_date=form.target_date.data,
                        target_time=form.target_time.data)
        db.session.add(new_task)
        db.session.commit()
        flash('Your task has been added.', 'success')
        return redirect(url_for('view_tasks', goal_id=goal_id, title=goal.goal))
    return render_template('goal-detail.html', form=form, goal=goal)

@app.route('/new_subtask/<task_id>', methods=['GET', 'POST'])
def new_subtask(task_id: str):
    form = TaskForm()
    form.submit.label.text = 'Add Subtask'
    parent_task = Task.query.filter_by(id=task_id).first()
    goal_id = parent_task.goal_id
    goal = Goal.query.filter_by(id=goal_id).first()
    if form.validate_on_submit():
        submitted_subtask = Task(form.goal.data,
                        goal_id=goal_id,
                        parent_id=task_id,
                        target_date=form.target_date.data,
                        target_time=form.target_time.data)
        db.session.add(submitted_subtask)
        db.session.commit()
        flash('Your task has been added.', 'success')        
        return redirect(url_for('view_tasks', goal_id=goal_id, title=goal.goal))
    return render_template('goal-detail.html', form=form, goal=goal)

@app.route('/goal/<goal_id>', methods=['GET', 'POST'])
def goal_detail(goal_id):
    goal = Goal.query.get(goal_id)
    form = DreamForm(obj=goal)
    form.submit.label.text = 'Update Dream'
    if form.validate_on_submit():
        goal.goal = form.goal.data
        goal.description = form.description.data
        goal.target_date = form.target_date.data
        goal.target_time = form.target_time.data
        db.session.commit()
        flash('Your dream has been updated.', 'success')
        return render_template('goal-detail.html', form=form, goal=goal)
        
    else:
        goal = Goal.query.get(goal_id)
        if goal is None:
            flash('Goal not found.', 'error')
            return redirect(url_for('dashboard'))
        else:
            print(goal.goal)
        form = DreamForm(obj=goal)
        form.submit.label.text = 'Update Dream'
        return render_template('goal-detail.html', form=form, goal=goal)
    
@app.route('/task/<task_id>', methods=['GET', 'POST'])
def task_detail(task_id):
    task = Task.query.get(task_id)
    form = TaskForm(obj=task)
    form.submit.label.text = 'Update Task'
    if form.validate_on_submit():
        task.task = form.goal.data
        task.target_date = form.target_date.data
        task.target_time = form.target_time.data
        db.session.commit()
        flash('Your task has been updated.', 'success')
        return render_template('goal-detail.html', form=form, goal=task)
        
    else:
        if task is None:
            flash('Task not found.', 'error')
            return redirect(url_for('dashboard'))
        else:
            print(task.task)
            form = TaskForm(obj=task)
            form.submit.label.text = 'Update Task'
            return render_template('goal-detail.html', form=form, goal=task)

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    goal_id = request.args.get('goal_id')
    goal = Goal.query.filter_by(id=goal_id).first()
    tasks = Task.query.filter_by(goal_id=goal_id).all()
    tasks = [task for task in tasks if task.parent_id is None]
    return render_template('view-tasks.html', goals=tasks, goal=goal, title=goal.goal, subtitle=None)

@app.route('/view_subtasks', methods=['GET'])
def view_subtasks():
    task_id = request.args.get('task_id')
    print(f'task id: {task_id}')
    task = Task.query.filter_by(id=task_id).first()
    goal = Goal.query.filter_by(id=task.goal_id).first()
    subtasks = Task.query.filter_by(parent_id=task_id).all()
    return render_template('view-subtasks.html', goal=goal, task=task, goals=subtasks, title=goal.goal, subtitle=task.task)

@app.route('/demo/generate_goals/<int:num_goals>/<string:title>/<string:goal_id>', methods=['GET', 'POST'])
def demo_goal_generation(num_goals, title, goal_id):
    print(f'num_goals: {num_goals}')
    print(f'title: {title}')
    print(f'goal_id: {goal_id}')
    goal = Goal.query.filter_by(id=goal_id).first()
    if title is None:
        title = goal.goal
    print(f'received goal: {goal.goal}')
    try:
        num_goals = int(num_goals)
        bot.generate_goals(goal, num_goals)        
    except Exception as e:
        print('exception when generating goals')
        print(e)
        return redirect(url_for('error_page', error_message=str(e)))
    try:
        tasks = Task.query.filter_by(goal_id=goal_id).all()
        print(f'tasks: {tasks}')
        print(f'goal: {goal.goal}')
        print(f'title: {title}')
        return render_template('generate_goals.html', goals=tasks, title=title, goal=goal)
    except Exception as e:
        print('exception when rendering template')
        print(e)        
        return redirect(url_for('error_page', error_message=str(e)))
    
@app.route('/generate_goals/<int:num_goals>', methods=['GET', 'POST'])
def goal_generation(num_goals):
    title = request.args.get('title')
    goal_id = request.args.get('goal_id')
    goal = Goal.query.filter_by(id=goal_id).first()
    if title is None:
        title = goal.goal
    try:
        num_goals = int(num_goals)
        bot.generate_goals(goal, num_goals)
        return redirect(url_for('view_tasks', goal_id=goal_id, title=title))
    except Exception as e:
        print('exception when generating goals')
        print(e)
        return redirect(url_for('error_page', error_message=str(e)))


@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/chat_api/<string:goal_id>', methods=['POST'])
def chat_api(goal_id):
    print("a POST request was made to chat")
    # task = Task.query.filter_by(id=task_id).first()
    goal = Goal.query.filter_by(id=goal_id).first()
    message = request.json['message']
    chat_bot = GoalChatBot(goal)
    response = chat_bot.get_response(message)
    return jsonify({'response': response})

@app.route('/task_chat_api/<string:task_id>', methods=['POST'])
def task_chat_api(task_id):
    task = Task.query.filter_by(id=task_id).first()
    goal = Goal.query.filter_by(id=task.goal_id).first()
    chat_bot = TaskChatBot(task, goal, [task.get_task() for task in task.subtasks])

@app.route('/goal/complete/<goal_id>', methods=['GET', 'POST'])
def complete_goal(goal_id):
    goal = Goal.query.filter_by(id=goal_id).first()
    goal.completed = not goal.completed
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/task/complete/<task_id>', methods=['GET', 'POST'])
def complete_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.completed = not task.completed
    db.session.commit()
    return redirect(url_for('view_tasks', goal_id=task.goal_id))


@app.route('/demo/display_subtasks/<string:task_id>', methods=['GET'])
def display_subtasks(task_id):    
    task = Task.query.filter_by(id=task_id).first()
    goal = Goal.query.filter_by(id=task.goal_id).first()
    if not task.subtasks:
        json = jsonify(error=f'No subtasks for task # {task_id}'), 404
        print(json)
        return json
    else:
        return render_template('generate_tasks.html', task=task, title=goal.goal, subtitle=task.task, goals=task.subtasks, goal=goal)
    
@app.route('/generate_subtasks/<int:num_subtasks>', methods=['GET', 'POST'])
def generate_subtasks(num_subtasks):
    task_id = request.args.get('task_id')
    task = Task.query.filter_by(id=task_id).first()
    bot.generate_subtasks(task, num_subtasks)
    return redirect(url_for('view_subtasks', task_id=task.id))

@app.route('/demo/generate_subtasks/<int:num_subtasks>', methods=['POST'])
def demo_generate_subtasks(num_subtasks):
    data = request.get_json()
    task_id = data['task_id']
    task = Task.query.filter_by(id=task_id).first()
    bot.generate_subtasks(task, num_subtasks)
    # get subtasks
    subtasks = Task.query.filter_by(parent_id=task_id).all()
    # convert subtasks to json
    subtasks_json = [subtask.to_dict() for subtask in subtasks]

    return jsonify(subtasks=subtasks_json)

#region API    
api = Api(app, version='1.0', doc='/api/api-docs', title='Pursuit Prophet API', description='Pursuit Prophet backend')

role_model = api.model('Role', {
    'role': fields.String(required=True, description="The user's primary goal"),
})

ns = api.namespace('api', description='Bot API')
@ns.route('/role')
class BotRole(Resource):
    @ns.expect(role_model, validate=True) 
    @ns.response(200, 'Role set successfully')
    @ns.response(400, 'Validation Error')
    def post(self):
        '''Set a new role for the bot'''
        role = request.json.get('role')
        bot.set_assistant_primary_goal(role)

        return {'role': f'{role}'}, 200
    
@ns.route('/goals')
class BotGoals(Resource):
    @ns.response(200, 'Goals generated successfully')
    def get(self):
        '''Generate goals for the bot'''
        if bot.io_manager.primary_goal is None:
            return {'error': 'Role not set, use /role first'}, 400
        
        goals = bot.generate_goals()
        return {'goals': f'{goals}'}, 200
#endregion API
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    if port is None:
        port = 5000
    app.debug = True
    socketio.run(app, host='0.0.0.0', port=port)
    