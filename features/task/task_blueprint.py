from app.models import Task, Goal
from app.pp_logging.db_logger import db
from flask import render_template, redirect, url_for, flash
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateField, TimeField
from wtforms.validators import DataRequired, Optional
from shared.blueprints.blueprints import task_bp 

class TaskForm(FlaskForm):
    goal = StringField('Task Name', validators=[DataRequired()], render_kw={"placeholder": "What do you need to do?"})
    target_date = DateField('Target Date', format='%Y-%m-%d', validators=[Optional()])
    target_time = TimeField('Target Time', format='%H:%M', validators=[Optional()])
    submit = SubmitField()

    def __init__(self, obj=None, **kwargs):
        super().__init__(obj=obj, **kwargs)
        if obj:
            self.goal.data = obj.task

@task_bp.route('/task/new_task/<goal_id>', methods=['GET', 'POST'])
def new_task(goal_id: str):
    form = TaskForm()
    form.submit.label.text = 'Add Task'
    goal = Goal.query.filter_by(id=goal_id).first()
    if form.validate_on_submit():
        new_task = Task(form.goal.data,
                        goal_id=goal_id,
                        target_date=form.target_date.data,
                        target_time=form.target_time.data)
        db.session.add(new_task)
        db.session.commit()
        flash('Your task has been added.', 'success')
        return redirect(url_for('view_tasks', goal_id=goal_id, title=goal.goal))
    return render_template('dream_db.dream-detail.html', form=form, goal=goal)

@task_bp.route('/task/<task_id>', methods=['GET', 'POST'])
def task_detail(task_id):
    task = Task.query.get(task_id)
    form = TaskForm(obj=task)
    form.submit.label.text = 'Update Task'
    if form.validate_on_submit():
        task.task = form.goal.data
        task.target_date = form.target_date.data
        task.target_time = form.target_time.data
        db.session.commit()
        flash('Your task has been updated.', 'success')
        return render_template('task-detail.html', form=form, goal=task)
        
    else:
        if task is None:
            flash('Task not found.', 'error')
            return redirect(url_for('dashboard'))
        else:
            print(task.task)
            form = TaskForm(obj=task)
            form.submit.label.text = 'Update Task'
            return render_template('task-detail.html', form=form, goal=task)
        