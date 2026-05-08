# roles.py

OWNERS = [
    6500594896,  # bu yerga o'zingizning Telegram ID'ingizni yozasiz
]


def is_owner(user_id):
    return user_id in OWNERS
