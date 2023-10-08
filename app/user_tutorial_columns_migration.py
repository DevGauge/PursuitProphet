from app.app import app as current_app, User
from .pp_logging.db_logger import db
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
import os


from sqlalchemy import text

def migrate():
    print('Initializing application context...')
    with current_app.app_context():
        DATABASE_URL = os.environ['DATABASE_URL']
        DATABASE_URL = DATABASE_URL[:8] + 'ql' + DATABASE_URL[8:]
        engine = create_engine(DATABASE_URL, echo=False)

        with engine.begin() as connection:
            table_name = 'user'
            print('DB connection established, adding columns...')

            # Adding columns to table
            for column in ["is_first_login", "is_first_detail_view", "is_first_new_goal", "is_first_new_task", "is_first_new_subtask", "is_first_demo_task_gen", "is_first_demo_subtask_gen", "is_demo_finished"]:
                connection.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS {column} boolean DEFAULT false'))

            print('Columns added')

            # Update each row with the default values
            print('Updating rows...')
            for column in ["is_first_login", "is_first_detail_view", "is_first_new_goal", "is_first_new_task", "is_first_new_subtask", "is_first_demo_task_gen", "is_first_demo_subtask_gen"]:
                connection.execute(text(f'UPDATE "{table_name}" SET {column}=true WHERE {column} IS NULL'))

            connection.execute(text(f'UPDATE "{table_name}" SET is_demo_finished=false WHERE is_demo_finished IS NULL'))

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