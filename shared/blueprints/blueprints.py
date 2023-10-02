from flask import Blueprint
demo_bp = Blueprint('demo_bp', __name__, template_folder='../../features/demo/templates')

def register_blueprints(flask_app):
    flask_app.register_blueprint(demo_bp)