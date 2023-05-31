import sys
from flask import Flask, render_template, request, redirect, url_for
from flask_restx import Api, Resource, fields

sys.path.append("..")
from bot import ChatBot

app = Flask(__name__)

bot = ChatBot()

api = Api(app, version='1.0', title='Bot API', description='A simple Bot API')

ns = api.namespace('bot', description='Bot operations')

role_model = api.model('Role', {
    'role': fields.String(required=True, description="The user's primary goal"),
})

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

@app.route('/', methods=['GET', 'POST'])
def welcome():
    if request.method == 'POST':        
        user_name = request.form.get('user_name')
        if user_name:  # checks if the field isn't empty
            return redirect(url_for('role_selection'))
    else:
        name = "PursuitProphet"
        return render_template('welcome.html', app_name=name)

@app.route('/role_selection', methods=['GET', 'POST'])
def role_selection():
    if request.method == 'POST':
        role = request.form.get('role')
        bot.set_assistant_primary_goal(role)
        return redirect(url_for('next_function'))  # replace 'next_function' with the name of your next route
    else:
        roles = ['Write a blog post about cats', 'Organize my house', 'Learn about quantum physics']
        return render_template('role_selection.html', roles=roles)

if __name__ == "__main__":
    app.run(debug=True)