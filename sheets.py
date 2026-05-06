import gspread
from config import SHEET_ID, GOOGLE_CREDENTIALS

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)

sheet = gc.open_by_key(SHEET_ID).worksheet("EduControl")


def get_report():
    try:
        row = sheet.row_values(15)

        if not row:
            return "❌ 15-qator bo'sh"

        result = "📊 15-QATOR:\n\n"

        for cell in row:
            result += f"{cell}\n"

        return result

    except Exception as e:
        return f"❌ Error:\n{e}"
