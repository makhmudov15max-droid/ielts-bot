import os

# Bot tokenini muhit o'zgaruvchisidan yoki default qiymatdan olish
BOT_TOKEN = os.getenv("BOT_TOKEN", "8679587093:***")

# Asosiy adminning telegram ID raqami
ADMIN_ID = int(os.getenv("ADMIN_ID", "6500594896"))

# Nazoratchi Guruh ID raqami
REPORTS_GROUP_ID = -1003608063747

# LMS Platformasi
LMS_BASE = "https://main.ieltszoneapp.uz"
LMS_EMAIL = os.getenv("LMS_EMAIL", "makhmudov15max@gmail.com")
import os as _os
LMS_KEY = _os.getenv("LMS_KEY", "Mahmudov02")
