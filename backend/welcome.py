import os
import sys
from flask import Flask, render_template, request, redirect, url_for
from flask_restx import Api, Resource, fields
import asyncio

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
        print(role)
        bot.set_assistant_primary_goal(role)
        return redirect(url_for('goal_generation'))  # replace 'next_function' with the name of your next route
    else:
        roles = ['Write a blog post about cats', 'Organize my house', 'Learn about quantum physics']
        return render_template('role_selection.html', roles=roles)

@app.route('/generate_goals')
def goal_generation():
    goals = bot.generate_goals()
    return render_template('generate_goals.html', goals=goals)

#region API    
api = Api(app, version='1.0', doc='/api-docs', title='Pursuit Prophet API', description='Pursuit Prophet backend')

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
#endregion API
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    if port is None:
        port = 5000
    app.run(host='0.0.0.0', port=port)
