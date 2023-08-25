from app.app import db, User

def migrate():
    # Query all existing rows
    rows_to_update = User.query.all()

    columns = [
        'is_first_login',
        'is_first_detail_view',
        'is_first_new_goal',
        'is_first_new_task',
        'is_first_new_subtask',
        'is_first_demo_task_gen',
        'is_first_demo_subtask_gen'
    ]

    # Update each row with the default values
    for row in rows_to_update:
        for column in columns:
            if getattr(row, column) is None:
                setattr(row, column, True)
        if getattr(row, 'is_demo_finished') is None:
            setattr(row, 'is_demo_finished', False)

    # Commit the changes
    db.session.commit()

def reset():
    rows_to_update = User.query.all()

    columns = [
        'is_first_login',
        'is_first_detail_view',
        'is_first_new_goal',
        'is_first_new_task',
        'is_first_new_subtask',
        'is_first_demo_task_gen',
        'is_first_demo_subtask_gen'
    ]

    # Update each row with the default values
    for row in rows_to_update:
        for column in columns:
            setattr(row, column, True)
        setattr(row, 'is_demo_finished', False)

    # Commit the changes
    db.session.commit()