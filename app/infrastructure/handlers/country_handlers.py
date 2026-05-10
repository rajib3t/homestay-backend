async def log_country_created_handler(event):
    """Basic handler for CountryCreatedEvent - logs the event creation"""
    print(f"Country created: {event.payload['country_id']} by user {event.payload['created_by']}")


async def log_country_updated_handler(event):
    """Basic handler for CountryUpdatedEvent - logs the event update"""
    print(f"Country updated: {event.payload['country_id']} by user {event.payload['updated_by']}")