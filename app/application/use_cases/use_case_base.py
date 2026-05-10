from app.deps.auth import CurrentUser

class UseCaseBase:
    def __init__(self, current_user: CurrentUser):
        self.current_user = current_user
        