# app/infrastructure/email/user_handlers.py

async def send_welcome_email_handler(event):
    from app.deps import get_email_service
    
    email_service = get_email_service()  # inject dependency

    user = event.user

    await email_service.send_welcome_email(
        to_email=user["email"],
        username=user["username"]
    )