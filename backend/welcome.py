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
from app.app import DreamForm
from app.app import db, app_instance
from flask_socketio import SocketIO, send, emit
from flask_security import roles_required, login_required, login_user, user_registered, current_user
from flask_security.confirmable import confirm_user, confirm_email_token_status
import uuid
from LangChainAgentFactory import AgentFactory
from langchain.tools import StructuredTool

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

@app.route('/error/<string:error_message>')
def error_page(error_message):
    return render_template('error.html', error_message=error_message)

@app.errorhandler(500)
def handle_500(error):
    return redirect(url_for('error_page', error_message=str(error)))

@app.route('/demo', methods=['GET', 'POST'])
def role_selection():
    if request.method == 'POST':
        role = request.form.get('role')
        goal_id = bot.set_assistant_primary_goal(role)
        return redirect(url_for('goal_generation', title=role, goal_id=goal_id))
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

@login_required
@app.route('/')
def dashboard():
    if current_user.is_authenticated:
        user_id = current_user.id
        user = app_instance.user_datastore.find_user(id=user_id)
        if user is not None:
            goals = Goal.query.filter_by(user_id=user_id).all()
            return render_template('dream-home.html', goals=goals)
        
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
        return redirect(url_for('view_tasks', goal_id=goal.id, title=goal.goal))
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

@app.route('/goal/<goal_id>', methods=['GET', 'POST'])
def goal_detail(goal_id):
    goal = Goal.query.get(goal_id)
    form = DreamForm(obj=goal)
    if form.validate_on_submit():        
        goal.goal = form.goal.data
        goal.description = form.description.data
        goal.target_date = form.target_date.data
        goal.target_time = form.target_time.data
        db.session.commit()
        flash('Your dream has been updated.', 'success')
        return redirect(url_for('dashboard'))
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
@app.route('/view_tasks', methods=['GET'])
def view_tasks():    
    goal_id = request.args.get('goal_id')
    goal = Goal.query.filter_by(id=goal_id).first()
    tasks = Task.query.filter_by(goal_id=goal_id).all()
    return render_template('view-tasks.html', goals=tasks, goal=goal, title=goal.goal)

@app.route('/view_subtasks', methods=['GET'])
def view_subtasks():
    task_id = request.args.get('goal_id')
    task = Task.query.filter_by(id=task_id).first()
    goal = Goal.query.filter_by(id=task.goal_id).first()
    subtasks = Task.query.filter_by(parent_id=task_id).all()
    return render_template('view-subtasks.html', goal=task, subtasks=subtasks, title=goal.goal, subtitle=task.task)
    

@app.route('/generate_goals', methods=['GET', 'POST'])
def goal_generation():
    title = request.args.get('title')
    goal_id = request.args.get('goal_id')
    goal = Goal.query.filter_by(id=goal_id).first()
    try:
        bot.generate_goals(goal)
        tasks = Task.query.filter_by(goal_id=goal_id).all()
        return render_template('generate_goals.html', goals=tasks, title=title)
    except Exception as e:
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

@app.route('/display_subtasks/<string:task_id>', methods=['GET'])
def display_subtasks(task_id):    
    task = Task.query.filter_by(id=task_id).first()
    goal = Goal.query.filter_by(id=task.goal_id).first()
    if not task.subtasks:
        json = jsonify(error=f'No subtasks for task # {task_id}'), 404
        print(json)
        return json
    else:
        return render_template('generate_tasks.html', task=task, subtasks=task.subtasks, goal=goal)
    
@app.route('/generate_subtasks', methods=['POST'])
def generate_subtasks():
    data = request.get_json()
    task_id = data['task_id']
    task = Task.query.filter_by(id=task_id).first()
    bot.generate_subtasks(task)
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
    socketio.run(app, host='0.0.0.0', port=port)
