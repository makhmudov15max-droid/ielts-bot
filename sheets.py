import gspread
from config import SHEET_ID, GOOGLE_CREDENTIALS

gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)

# SHEETS
edu_sheet = gc.open_by_key(SHEET_ID).worksheet("EduControl")
teacher_sheet = gc.open_by_key(SHEET_ID).worksheet("Ustozlar")


# IELTS SCORE OLISH
def get_teacher_score(teacher_name):

    data = teacher_sheet.get_all_values()

    for row in data[1:]:

        name = row[0].strip()
        score = row[1].strip()

        if name == teacher_name:
            return score

    return None


# IELTS SCORE UPDATE
def update_teacher_score(teacher_name, new_score):

    data = teacher_sheet.get_all_values()

    for index, row in enumerate(data[1:], start=2):

        name = row[0].strip()

        if name == teacher_name:

            teacher_sheet.update(
                f"B{index}",
                [[new_score]]
            )

            return True

    return False
