import logging
from datetime import date, datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

db = SQLAlchemy()
class Log(db.Model):
    __tablename__ = 'log'
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20))
    message = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, level, message):
        self.level = level
        self.message = message

Base = declarative_base()

class DBLogger(logging.Handler):
    level = logging.INFO

    def __init__(self, db, *args, **kwargs):
        super(DBLogger, self).__init__(*args, **kwargs)
        self.db = db

    def emit(self, record):
        """Flask log handler"""
        message = self.format(record)
        level = record.levelname
        self.log(message, level)

    def format(self, record):
        """Format the message into a string."""
        return f'[{record.levelname.upper()}]: {record.getMessage()}'

    def create_table_if_not_exists(self):
        """Create the log table if it doesn't exist."""
        Base.metadata.create_all(self.db.engine)

    def log(self, message, level='INFO'):
        """Logs a message with a given level."""
        log_entry = Log(level=level, message=message)
        self.db.session.add(log_entry)
        self.db.session.commit()

# Example usage:
# from flask_sqlalchemy import SQLAlchemy

# db = SQLAlchemy(app) # where 'app' is your Flask app
# logger = DBLogger(db)
# logger.log('This is a test message.')
