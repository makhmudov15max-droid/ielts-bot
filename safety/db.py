import json


USERS_FILE = "safety/database/users.json"
PENDING_FILE = "safety/database/pending_users.json"


def load_users():
    with open(USERS_FILE, "r") as file:
        return json.load(file)


def save_users(data):
    with open(USERS_FILE, "w") as file:
        json.dump(data, file, indent=4)


def load_pending():
    with open(PENDING_FILE, "r") as file:
        return json.load(file)


def save_pending(data):
    with open(PENDING_FILE, "w") as file:
        json.dump(data, file, indent=4)
