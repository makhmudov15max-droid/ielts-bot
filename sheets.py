import gspread
from config import SHEET_ID, GOOGLE_CREDENTIALS

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)

sheet = gc.open_by_key(SHEET_ID).sheet1


def get_report():
    try:
        value = sheet.get("I15", value_render_option="FORMATTED_VALUE")[0][0]

        return f"📊 I15:\n{value}"

    except Exception as e:
        return f"❌ Error:\n{e}"
