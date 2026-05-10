import json


def load_users():
    with open("database/users.json", "r") as file:
        return json.load(file)


def save_users(data):
    with open("database/users.json", "w") as file:
        json.dump(data, file, indent=4)


def load_pending():
    with open("database/pending_users.json", "r") as file:
        return json.load(file)


def save_pending(data):
    with open("database/pending_users.json", "w") as file:
        json.dump(data, file, indent=4)
