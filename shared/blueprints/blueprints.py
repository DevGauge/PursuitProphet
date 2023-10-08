from flask import Blueprint
demo_bp = Blueprint('demo_bp', __name__, template_folder='../../features/demo/templates')
dream_bp = Blueprint('dream_bp', __name__, template_folder='../../features/dream/templates')
task_bp = Blueprint('task_bp', __name__, template_folder='../../features/task/templates')

def register_blueprints(flask_app):
    blueprints = [demo_bp, dream_bp, task_bp]
    for blueprint in blueprints:
        flask_app.register_blueprint(blueprint)
        print(f'registered blueprint: {blueprint.name} with url_prefix: {blueprint.url_prefix}')