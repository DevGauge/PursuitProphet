from app.models import Goal, Task
from app.pp_logging.db_logger import db
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateField, TimeField
from wtforms.validators import DataRequired, Optional
from shared.blueprints.blueprints import dream_bp

class DreamForm(FlaskForm):
    goal = StringField('Dream Name', validators=[DataRequired()], render_kw={"placeholder": "What are you dreaming of?"})
    description = TextAreaField('Dream Description', validators=[Optional()], render_kw={"placeholder": "Describe your dream"})
    target_date = DateField('Target Date', format='%Y-%m-%d', validators=[Optional()])
    target_time = TimeField('Target Time', format='%H:%M', validators=[Optional()])
    submit = SubmitField()

    def __init__(self, obj=None, **kwargs):
        super().__init__(obj=obj, **kwargs)

@dream_bp.route('/dream/add_dream', methods=['GET', 'POST'])
def add_dream():
    form = DreamForm()
    form.submit.label.text = 'Add Dream'
    if form.validate_on_submit():
        new_goal = Goal(form.goal.data, 
                        user_id=current_user.id, 
                        description=form.description.data,
                        target_date=form.target_date.data, 
                        target_time=form.target_time.data)
        db.session.add(new_goal)
        db.session.commit()
        flash('Your dream has been added.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('dream-detail.html', form=form, goal=None)

@dream_bp.route('/dream/<goal_id>', methods=['GET', 'POST'])
def view_dream(goal_id: str):
    goal = Goal.query.get(goal_id)
    form = DreamForm(obj=goal)
    form.submit.label.text = 'Update Dream'
    if form.validate_on_submit():
        goal.goal = form.goal.data
        goal.description = form.description.data
        goal.target_date = form.target_date.data
        goal.target_time = form.target_time.data
        db.session.commit()
        flash('Your dream has been updated.', 'success')
        return render_template('dream-detail.html', form=form, goal=goal)
    return render_template('dream-detail.html', form=form, goal=goal)

@dream_bp.route('/dream/complete/<goal_id>', methods=['GET', 'POST'])
def complete_dream(goal_id):
    goal = Goal.query.filter_by(id=goal_id).first()
    goal.completed = not goal.completed
    db.session.commit()
    return redirect(url_for('dashboard'))

@dream_bp.route('/view_tasks', methods=['GET'])
def view_tasks():
    goal_id = request.args.get('goal_id')
    print(f'goal id: {goal_id}')
    goal = Goal.query.filter_by(id=goal_id).first()
    tasks = Task.query.filter_by(goal_id=goal_id).all()
    tasks = [task for task in tasks if task.parent_id is None]
    return render_template('view-tasks.html', goals=tasks, goal=goal, title=goal.goal, subtitle=None, pageTitle=goal.goal)