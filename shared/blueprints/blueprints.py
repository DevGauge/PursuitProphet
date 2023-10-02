from flask import Blueprint
task_bp = Blueprint('task_bp', __name__, template_folder='../../features/demo/templates')

def register_blueprints(flask_app):
    flask_app.register_blueprint(task_bp)