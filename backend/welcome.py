import os
import sys
from flask import Flask, render_template, request, redirect, url_for
from flask_restx import Api, Resource, fields
from flask import jsonify

sys.path.append("..")
from bot import ChatBot

app = Flask(__name__)

bot = ChatBot()

@app.route('/', methods=['GET', 'POST'])
def welcome():
    if request.method == 'POST':
        print('bar')
        user_name = request.form.get('user_name')
        if user_name:  # checks if the field isn't empty
            return redirect(url_for('role_selection'))
    else:
        print('foo')
        name = "Pursuit Prophet"
        return render_template('welcome.html', app_name=name)

@app.route('/role_selection', methods=['GET', 'POST'])
def role_selection():
    if request.method == 'POST':
        role = request.form.get('role')
        bot.set_assistant_primary_goal(role)
        return redirect(url_for('goal_generation', title=role))  # replace 'next_function' with the name of your next route
    else:
        roles = ['Write a blog post about cats', 'Organize my house', 'Learn about quantum physics']
        return render_template('role_selection.html', roles=roles)

@app.route('/generate_goals', methods=['GET', 'POST'])
def goal_generation():
    title = request.args.get('title')
    goals = bot.generate_goals()
    return render_template('generate_goals.html', goals=goals, title=title)

# route for rendering subtasks for a given task. Endpoint should be dynamic like /display_subtasks/<task_id>
@app.route('/display_subtasks/<int:goal_id>', methods=['GET'])
def display_subtasks(goal_id):    
    goal = bot.goal_manager.goals[goal_id]
    subtasks = goal.tasks
    if subtasks is None:
        json = jsonify(error=f'No subtasks for goal # {goal_id}'), 404
        print(json)
        return json
    else:
        return render_template('generate_tasks.html', subtasks=subtasks, goal=goal)
    
# route for generating subtasks for a given task
@app.route('/generate_subtasks', methods=['POST'])
def generate_subtasks():
    print('hit')
    data = request.get_json()
    print(f'data: {data}')
    goal_id = int(data['goal_id']) - 1
    
    if goal_id < 0 or goal_id > len(bot.goal_manager.goals):
        return jsonify(error='Goal ID not found'), 400
    
    # Generate subtasks for the goal with the given ID.
    bot.generate_subtasks(goal_id)
    # get subtasks
    subtasks = bot.goal_manager.goals[goal_id].tasks
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
