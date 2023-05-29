import sys
from flask import Flask, render_template, request, redirect, url_for

sys.path.append("..")
from bot import ChatBot


app = Flask(__name__)

bot = ChatBot()

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