from flask import Blueprint

def construct_blueprint(name: str, template_folder: str = None):
    """Constructs a blueprint with the given name and template_folder, which defaults to the name"""
    if template_folder is None:
        template_folder = name
    return Blueprint(name + '_bp', __name__, template_folder='../../features/' + template_folder + '/templates')

demo_bp = construct_blueprint('demo')
dream_bp = construct_blueprint('dream')
task_bp = construct_blueprint('task')
subtask_bp = construct_blueprint('subtask')

def register_blueprints(flask_app):
    blueprints = [demo_bp, dream_bp, task_bp, subtask_bp]
    for blueprint in blueprints:
        flask_app.register_blueprint(blueprint)
        print(f'registered blueprint: {blueprint.name} with url_prefix: {blueprint.url_prefix}')