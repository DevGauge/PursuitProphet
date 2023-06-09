import os
import sys
from flask import Flask, jsonify, render_template, request, redirect, url_for, send_from_directory
from flask_restx import Api, Resource, fields
sys.path.insert(0, '../')
sys.path.insert(0, '/app')
from bot import ChatBot
from langchain_m.langchain_module import TaskChatBot
import app.app
from app.app import Goal, Task, User 
from app.app import LoginForm, RegistrationForm
from app.app import db, app_instance
from flask_socketio import SocketIO, send, emit
from flask_security import roles_required, login_required, login_user, current_user
from flask_security.confirmable import confirm_user, confirm_email_token_status
import uuid

app = app_instance.app
socketio = SocketIO(app)

bot = ChatBot()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)
    send(data, broadcast=True)
    
# @app.route('/node_modules/<path:filename>')
# def custom_static(filename):
#     print('static node filename: ', filename)
#     return send_from_directory(os.path.join(app.root_path, '..', 'node_modules'), filename)

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

@app.route('/new_dream', methods=['GET', 'POST'])
def new_dream():
    goals = Goal.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        dream = request.form.get('dream')
        goal = Goal(user_input=dream, user_id=current_user.id)
        db.session.add(goal)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    elif request.method == 'GET' and request.args.get('cancel'):
        return redirect(url_for('dashboard'))
    
    return render_template('new_dream.html', goals=goals)

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

@app.route('/chat_api/<string:task_id>', methods=['POST'])
def chat_api(task_id):
    task = Task.query.filter_by(id=task_id).first()
    goal = Goal.query.filter_by(id=task.goal_id).first()
    message = request.json['message']
    chat_bot = TaskChatBot(task, goal, [task.get_task() for task in task.subtasks])
    response = chat_bot.get_response(message)
    return jsonify({'response': response})

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
    print(f'data: {data}')
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
