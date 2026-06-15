from models import User
from utils import format_currency


class UserService:
    def create_user(self, name: str, email: str) -> User:
        user = User(name, email)
        return user

    def get_display(self, user: User) -> str:
        return user.get_display_name()

    def validate_user(self, user: User) -> bool:
        return user.validate()

    def format_price(self, amount: float) -> str:
        return format_currency(amount)
