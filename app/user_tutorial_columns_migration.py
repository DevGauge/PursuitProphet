from app.app import db, User
from flask import current_app


def migrate():
    with current_app.app_context():
        # Query all existing rows
        print('Migrating user tutorial columns...')
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

        print('Committing changes...')

        # Commit the changes
        db.session.commit()
        print('Migration successful')

def reset():
    print('Resetting user tutorial columns...')
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
    return jsonify({'message': 'Reset successful'}), 200

if __name__ == '__main__':
    migrate()