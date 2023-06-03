import os
import sys
from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_restx import Api, Resource, fields
sys.path.insert(0, '../')
sys.path.insert(0, '/app')
from bot import ChatBot
import app.app
from app.app import Goal, Task
bot = ChatBot()

app = app.app.app

# @app.route('/', methods=['GET', 'POST'])
# def welcome():
#     if request.method == 'POST':
#         print('bar')
#         user_name = request.form.get('user_name')
#         if user_name:  # checks if the field isn't empty
#             return redirect(url_for('role_selection'))
#     else:
#         print('foo')
#         name = "Pursuit Prophet"
#         return render_template('welcome.html', app_name=name)

@app.route('/', methods=['GET', 'POST'])
def role_selection():
    if request.method == 'POST':
        role = request.form.get('role')
        goal_id = bot.set_assistant_primary_goal(role)
        # goal = Goal.query.filter_by(goal=role).first() # TODO: filter by goal id
        return redirect(url_for('goal_generation', title=role, goal_id=goal_id))  # replace 'next_function' with the name of your next route
    else:
        roles = ['Write a blog post about cats', 'Organize my house', 'Learn about quantum physics']
        return render_template('role_selection.html', roles=roles)

@app.route('/generate_goals', methods=['GET', 'POST'])
def goal_generation():
    title = request.args.get('title')
    goal_id = request.args.get('goal_id')
    goal = Goal.query.filter_by(id=goal_id).first()
    bot.generate_goals(goal)
    tasks = Task.query.filter_by(goal_id=goal_id).all()
    return render_template('generate_goals.html', goals=tasks, title=title)

# route for rendering subtasks for a given task. Endpoint should be dynamic like /display_subtasks/<task_id>
@app.route('/display_subtasks/<string:task_id>', methods=['GET'])
def display_subtasks(task_id):    
    task = Task.query.filter_by(id=task_id).first()
    goal = Goal.query.filter_by(id=task.goal_id).first()
    if not task.subtasks:
        json = jsonify(error=f'No subtasks for task # {task_id}'), 404
        print(json)
        return json
    else:
        return render_template('generate_tasks.html', subtasks=task.subtasks, goal=goal)
    
# route for generating subtasks for a given task
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
    app.run(host='0.0.0.0', port=port)
