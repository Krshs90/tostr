import models as m
from services.user_service import UserService as US

service = US()


def run():
    user = m.User("Alice", "alice@example.com")
    display = service.get_display(user)
    return display
