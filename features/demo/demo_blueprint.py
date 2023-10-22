from flask import render_template, request, redirect, url_for, jsonify
from app.models import Task, Goal, ChatBot
from shared.blueprints.blueprints import demo_bp
from bot import IOManager, GoalGeneratorBot, GoalManager

io_manager = IOManager()
goal_manager = GoalManager(io_manager)
goal_gen_bot = GoalGeneratorBot('', num_goals=10)
gen_bot = ChatBot(goal_manager, goal_gen_bot)


@demo_bp.route('/demo', methods=['GET', 'POST'])
def role_selection():
    if request.method == 'POST':
        role = request.form.get('role')
        print(f'setting role to: {role}')
        goal_id = gen_bot.set_assistant_primary_goal(role)
        print(f'goal_id for primary role: {goal_id}')
        return redirect(url_for('demo_bp.demo_goal_generation', num_goals=10, title=role, page_title=role, goal_id=goal_id))
    else:
        roles = ['Write a blog post about cats', 'Organize my house', 'Learn about quantum physics']
        return render_template('role_selection.html', roles=roles, pageTitle="Pursuit Prophet Dream Demo")

@demo_bp.route('/demo/generate_tasks/<int:num_goals>/<string:title>/<string:goal_id>', methods=['GET', 'POST'])
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
        gen_bot.generate_goals(goal, num_goals)
    except Exception as e:
        print('exception when generating goals')
        print(e)
        return redirect(url_for('error_page', error_message=str(e)))
    try:
        tasks = Task.query.filter_by(goal_id=goal_id).all()
        print(f'tasks: {tasks}')
        print(f'goal: {goal.goal}')
        print(f'title: {title}')
        return render_template('task-view.html', goals=tasks, title=title, goal=goal, pageTitle=title)
    except Exception as e:
        print('exception when rendering template')
        print(e)        
        return redirect(url_for('error_page', error_message=str(e)))

@demo_bp.route('/demo/display_subtasks/<string:task_id>', methods=['GET'])
def display_subtasks(task_id):    
    task = Task.query.filter_by(id=task_id).first()
    goal = Goal.query.filter_by(id=task.goal_id).first()
    if not task.subtasks:
        json = jsonify(error=f'No subtasks for task # {task_id}'), 404
        print(json)
        return json    
    return render_template('subtask-view.html', task=task, title=goal.goal, subtitle=task.task, goals=task.subtasks, goal=goal)

@demo_bp.route('/demo/generate_subtasks/<int:num_subtasks>', methods=['POST'])
def demo_generate_subtasks(num_subtasks):
    data = request.get_json()
    task_id = data['task_id']
    task = Task.query.filter_by(id=task_id).first()
    gen_bot.generate_subtasks(task, num_subtasks)
    # get subtasks
    subtasks = Task.query.filter_by(parent_id=task_id).all()
    # convert subtasks to json
    subtasks_json = [subtask.to_dict() for subtask in subtasks]

    return jsonify(subtasks=subtasks_json)
