class User:
    name: str
    email: str

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def get_display_name(self) -> str:
        return f"{self.name} <{self.email}>"

    def validate(self) -> bool:
        return self.check_name() and self.check_email()

    def check_name(self) -> bool:
        return len(self.name) > 0

    def check_email(self) -> bool:
        return "@" in self.email


class Product:
    title: str
    price: float

    def __init__(self, title: str, price: float):
        self.title = title
        self.price = price

    def apply_discount(self, rate: float) -> float:
        return self.price * (1 - rate)
