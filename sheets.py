import gspread
from config import SHEET_ID, GOOGLE_CREDENTIALS

# GOOGLE SHEETS CONNECT
gc = gspread.service_account_from_dict(GOOGLE_CREDENTIALS)

# SHEETS
edu_sheet = gc.open_by_key(SHEET_ID).worksheet("EduControl")
teacher_sheet = gc.open_by_key(SHEET_ID).worksheet("Ustozlar")


# IELTS SCORE OLISH
def get_teacher_score(teacher_name):

    data = teacher_sheet.get_all_values()

    for row in data[1:]:

        if len(row) < 2:
            continue

        name = row[0].strip()
        score = row[1].strip()

        if name == teacher_name:
            return score

    return None


# IELTS SCORE UPDATE
def update_teacher_score(teacher_name, new_score):

    data = teacher_sheet.get_all_values()

    for index, row in enumerate(data[1:], start=2):

        if len(row) < 2:
            continue

        name = row[0].strip()

        if name == teacher_name:

            teacher_sheet.update(
                f"B{index}",
                [[new_score]]
            )

            return True

    return False


# DAILY REPORT
def get_report():

    try:

        data = edu_sheet.get_all_values()

        report = "📊 DAILY REPORT\n\n"

        found = False

        for row in data[2:]:

            try:

                if len(row) < 10:
                    continue

                # C,D,E,H,I,J
                teacher = row[2].strip()
                group_name = row[3].strip()
                level = row[4].strip()

                days_left = row[7].strip()

                status = row[8].strip()
                comment = row[9].strip()

                # DAYS LEFT
                if not days_left.isdigit():
                    continue

                days_left = int(days_left)

                # 14 kundan katta bo'lsa skip
                if days_left > 14:
                    continue

                # IELTS FILTER
                allowed_levels = [
                    "IELTS Standard",
                    "IELTS Expert",
                    "IELTS Intensive"
                ]

                novice_warning = False

                # IELTS NOVICE
                if level == "IELTS Novice":

                    teacher_score = get_teacher_score(teacher)

                    # FAQAT 8.0 teacher
                    if teacher_score == "8.0":
                        novice_warning = True
                    else:
                        continue

                # GENERAL ENGLISH SKIP
                elif level not in allowed_levels:
                    continue

                found = True

                # EMOJI
                if days_left <= 7:
                    emoji = "🔴"
                else:
                    emoji = "🟡"

                # REPORT
                report += f"{emoji} {group_name} ({level})\n"

                report += f"👨‍🏫 {teacher}\n"

                report += f"⏳ {days_left} kun qoldi\n"

                # NOVICE WARNING
                if novice_warning:
                    report += "⚠️ Boshqa ustoz topish kerak\n"

                # STATUS
                if status:
                    report += f"📌 {status}\n"

                # COMMENT
                if comment:
                    report += f"💬 {comment}\n"

                report += "\n"

            except:
                continue

        if not found:
            return "📊 Hozircha muammo yo'q"

        return report

    except Exception as e:
        return f"❌ Error:\n{e}"
