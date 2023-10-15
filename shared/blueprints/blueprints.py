import os
from flask import Blueprint

def construct_blueprint(name: str):
    """Constructs a blueprint with the given name and template_folder, which defaults to the name"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.abspath(os.path.join(current_dir, '../../features'))
    template_path = os.path.join(root_path, name, 'templates')
    static_path = os.path.join(root_path, name, 'static')
    
    return Blueprint(name + '_bp', __name__, template_folder=template_path, static_folder=static_path, static_url_path=f'/{name}_static')

demo_bp = construct_blueprint('demo')
dream_bp = construct_blueprint('dream')
task_bp = construct_blueprint('task')
subtask_bp = construct_blueprint('subtask')

def register_blueprints(flask_app):
    blueprints = [demo_bp, dream_bp, task_bp, subtask_bp]
    for blueprint in blueprints:
        flask_app.register_blueprint(blueprint)
        print(f'registered blueprint: {blueprint.name} with url_prefix: {blueprint.url_prefix}, template_folder: {blueprint.template_folder}, static_folder: {blueprint.static_folder}')
