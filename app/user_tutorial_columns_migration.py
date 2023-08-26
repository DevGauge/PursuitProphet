from app.app import app as current_app
from app.app import db, User
from sqlalchemy import create_engine, MetaData, Table
import os


from sqlalchemy import text

def migrate():
    with current_app.app_context():
        DATABASE_URL = os.environ['DATABASE_URL']
        DATABASE_URL = DATABASE_URL[:8]+'ql' + DATABASE_URL[8:]
        engine = create_engine(DATABASE_URL)
        metadata = MetaData()

        table_name = 'user'

       def migrate():
    print('Initializing application context...')
    with current_app.app_context():
        DATABASE_URL = os.environ['DATABASE_URL']
        DATABASE_URL = DATABASE_URL[:8]+'ql' + DATABASE_URL[8:]
        engine = create_engine(DATABASE_URL)
        metadata = MetaData()

        table_name = 'user'
        user_table = Table(table_name, metadata, autoload_with=engine)
        print('Application context initialized')

        # Adding columns to table
        connection = engine.connect()
        print('DB connection established, adding columns...')
        for column in ["is_first_login", "is_first_detail_view", "is_first_new_goal", "is_first_new_task", "is_first_new_subtask", "is_first_demo_task_gen", "is_first_demo_subtask_gen", "is_demo_finished"]:
            connection.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS {column} boolean DEFAULT false'))
        connection.close()
        print('Columns added')

        # Query all existing rows
        print('Migrating user tutorial columns...')
        rows_to_update = User.query.all()
        print('User rows queried')

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
        print('Updating rows...')
        for row in rows_to_update:
            print(f'Updating row {row.id}...')
            for column in columns:
                if getattr(row, column) is None:
                    setattr(row, column, True)
            if getattr(row, 'is_demo_finished') is None:
                setattr(row, 'is_demo_finished', False)
            db.session.commit()
            print(f'Row {row.id} updated')  

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