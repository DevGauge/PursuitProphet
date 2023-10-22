from shared.blueprints.blueprints import subtask_bp
from flask import render_template, redirect, url_for, flash
from app.models import Task, Goal
from app.pp_logging.db_logger import db
from features.task.task_blueprint import TaskForm

@subtask_bp.route('/subtask/<subtask_id>', methods=['GET', 'POST'])
def subtask_detail(subtask_id):
    subtask = Task.query.get(subtask_id)
    task = Task.query.filter_by(id=subtask.parent_id).first()

    goal = Goal.query.filter_by(id=task.goal_id).first()
    form = TaskForm(obj=subtask)
    form.submit.label.text = 'Update Subtask'
    if form.validate_on_submit():
        subtask.task = form.goal.data
        subtask.target_date = form.target_date.data
        subtask.target_time = form.target_time.data
        db.session.commit()
        flash('Your subtask has been updated.', 'success')
        return render_template('subtask-detail.html', form=form, task=task, subtask=subtask, goal=goal)
    else:
        if subtask is None:
            flash('Subtask not found.', 'error')
            return redirect(url_for('dashboard'))
        else:
            return render_template('subtask-detail.html', form=form, task=task, subtask=subtask, goal=goal)

@subtask_bp.route('/subtask/delete/<subtask_id>', methods=['GET', 'POST'])
def delete_subtask(subtask_id):
    subtask=Task.query.filter_by(id=subtask_id).first()
    print(f'subtask parent id: {subtask.parent_id}')
    task = Task.query.filter_by(id=subtask.parent_id).first()
    goal = Goal.query.filter_by(id=task.goal_id).first()
    if subtask is None:
        flash('Subtask not found.', 'error')
        print("subtask not found")
        return redirect(url_for('dashboard'))
    else:
        db.session.delete(subtask)
        db.session.commit()
        flash('Your task has been deleted.', 'success')
    if task is not None:
        print(f"task and subtask found: {task.task}\n{subtask.task}")
        return redirect(url_for('task_bp.view_subtasks', task_id=task.id, title=goal.goal))
    else:
        print(f'goal with id {task.goal_id} not found')
        return redirect(url_for('dashboard'))

@subtask_bp.route('/new_subtask/<task_id>', methods=['GET', 'POST'])
def new_subtask(task_id: str):
    form = TaskForm()
    form.submit.label.text = 'Add Subtask'
    parent_task = Task.query.filter_by(id=task_id).first()
    goal_id = parent_task.goal_id
    goal = Goal.query.filter_by(id=goal_id).first()
    if form.validate_on_submit():
        submitted_subtask = Task(form.goal.data,
                        goal_id=goal_id,
                        parent_id=task_id,
                        target_date=form.target_date.data,
                        target_time=form.target_time.data)
        db.session.add(submitted_subtask)
        db.session.commit()
        flash('Your subtask has been added.', 'success')        
        return redirect(url_for('task_bp.view_subtasks', task_id=task_id, title=goal.goal))
    return render_template('subtask-detail.html', form=form, goal=goal, task=parent_task)
