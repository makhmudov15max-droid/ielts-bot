import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USERS_FILE = os.path.join(BASE_DIR, "database", "users.json")
PENDING_FILE = os.path.join(BASE_DIR, "database", "pending_users.json")
BLOCKED_FILE = os.path.join(BASE_DIR, "database", "blocked_users.json")


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


def load_blocked():
    with open(BLOCKED_FILE, "r") as file:
        return json.load(file)


def save_blocked(data):
    with open(BLOCKED_FILE, "w") as file:
        json.dump(data, file, indent=4)
