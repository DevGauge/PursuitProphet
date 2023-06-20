import os
import sys
from flask import Flask, jsonify, render_template, request, redirect, url_for
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
from flask_security import roles_required, login_required
import uuid

app = app_instance.app
socketio = SocketIO(app)

bot = ChatBot()

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

@app.route('/', methods=['GET', 'POST'])
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

@app.route('/register', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('dashboard', user_id=user.id))
    else:
        return render_template('register.html', form=RegistrationForm())
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')        
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            return redirect(url_for('error_page', error_message='Invalid email or password'))
        else:
            return redirect(url_for('dashboard', user_id=user.id))
    else:
        return render_template('login.html', form=LoginForm())

@login_required
@app.route('/dashboard/<string:user_id>')
def dashboard(user_id):
    goals = Goal.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', goals=goals)

@app.route('/generate_goals', methods=['GET', 'POST'])
def goal_generation():
    title = request.args.get('title')
    goal_id = request.args.get('goal_id')
    goal = Goal.query.filter_by(id=goal_id).first()
    try:
        bot.generate_goals(goal)
        tasks = Task.query.filter_by(goal_id=goal_id).all()
    except Exception as e:
        print(e)
        return redirect(url_for('error_page', error_message=str(e)))
    finally:
        return render_template('generate_goals.html', goals=tasks, title=title)

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
    
    # Convert the subtasks to a format that can be sent as JSON.
    # This might not be necessary if your subtasks are already in a suitable format.
    # subtasks_json = [subtask.to_dict() for subtask in subtasks]
    
    # Send the subtasks back to the client.
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
