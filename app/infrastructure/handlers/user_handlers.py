async def log_user_updated_handler(event):
    """Basic handler for UserUpdatedEvent - logs the user update"""
    print(f"User updated: {event.payload['user_id']} by user {event.payload['updated_by']}")