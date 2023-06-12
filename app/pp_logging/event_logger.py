class EventLogger:

    def __init__(self, db_logger):
        self.db_logger = db_logger

    def sanitize_event(self, event, attributes):
        """Sanitize the event and attributes to ensure they are suitable for the database."""

        # Check the event format
        if not isinstance(event, str):
            raise ValueError('Event must be a string.')
        if not isinstance(attributes, dict):
            raise ValueError('Attributes must be a dictionary.')

        # Convert all attribute values to strings
        attributes = {k: str(v) for k, v in attributes.items()}

        return event, attributes

    def log_event(self, event, attributes, level='INFO'):
        """Log an event with associated attributes."""

        # Sanitize the event and attributes
        event, attributes = self.sanitize_event(event, attributes)

        # Convert the attributes dictionary into a string
        attributes_str = ', '.join(f'{k}: {v}' for k, v in attributes.items())

        # Log the event and attributes
        self.db_logger.log(f"Event: {event}. Attributes: {attributes_str}", level)