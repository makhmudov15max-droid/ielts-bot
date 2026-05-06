import gspread
from config import SHEET_ID, GOOGLE_CREDENTIALS

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)

sheet = gc.open_by_key(SHEET_ID).worksheet("EduControl")


def get_report():
    try:
        value = sheet.acell("I15").value

        return f"📊 I15:\n{value}"

    except Exception as e:
        return f"❌ Error:\n{e}"
