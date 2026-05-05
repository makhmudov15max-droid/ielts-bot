import os, json

BOT_TOKEN = os.environ["BOT_TOKEN"]
SHEET_ID  = os.environ["SHEET_ID"]

_raw = os.environ["GOOGLE_CREDENTIALS"]
GOOGLE_CREDENTIALS = json.loads(_raw)
