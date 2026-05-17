# calculators/cashier_calc.py

def calculate_cashier_salary(data: dict) -> dict:
    hours = float(data.get("hours", 0))
    days = float(data.get("days", 0))
    cover_hours = float(data.get("cover_hours", 0))
    missed_hours = float(data.get("missed_hours", 0))
    
    active_students = float(data.get("active_students", 0))
    active_debtors = float(data.get("active_debtors", 0))
    archive_students = float(data.get("archive_students", 0))
    archive_debtors = float(data.get("archive_debtors", 0))

    # ⏰ Fixa / Ishbay qismi (Soatbay stavka)
    if hours <= 8:
        daily_salary = hours * 15000
    else:
        extra_hours = hours - 8
        daily_salary = (8 * 15000) + (extra_hours * 20000)

    worked_salary = daily_salary * days

    # 📊 Talabalar va qarzdorlik foiz hisobi
    total_students = active_students + archive_students
    total_debtors = active_debtors + archive_debtors
    debt_percentage = (total_debtors * 100 / total_students) if total_students > 0 else 0

    # 🎯 Rasmga asosan yangi ko'paytiruvchi (Multiplier) mantiqi
    if debt_percentage == 0:
        multiplier = 3.0
        status_text = "O'ta go'zal (3.0x)"
    elif debt_percentage <= 2.0:
        multiplier = 2.0
        status_text = "Zo'r (2.0x)"
    elif debt_percentage <= 5.0:
        multiplier = 1.8
        status_text = "Yaxshi (1.8x)"
    elif debt_percentage <= 7.0:
        multiplier = 1.7
        status_text = "Yomon emas (1.7x)"
    elif debt_percentage <= 10.0:
        multiplier = 1.6
        status_text = "Qoniqarsiz (1.6x)"
    elif debt_percentage <= 15.0:
        multiplier = 1.5
        status_text = "Yomon (1.5x)"
    elif debt_percentage <= 20.0:
        multiplier = 1.4
        status_text = "Juda yomon (1.4x)"
    elif debt_percentage <= 30.0:
        multiplier = 1.2
        status_text = "Qo'rqinchli (1.2x)"
    else:
        multiplier = 1.0
        status_text = "Qil ustidasiz (1.0x)"

    # 💸 Jami summani karrali ko'paytirish
    multiplied_salary = worked_salary * multiplier
    kpi_bonus_profit = multiplied_salary - worked_salary

    # 🔄 Cover bonus va ish qoldirish jarimasi
    cover_bonus = cover_hours * 15000
    missed_penalty = missed_hours * 15000

    # 🏁 Yakuniy oylik formula
    total_salary = multiplied_salary + cover_bonus - missed_penalty

    return {
        "worked_salary": int(worked_salary),
        "multiplier": multiplier,
        "status_text": status_text,
        "kpi_bonus_profit": int(kpi_bonus_profit),
        "cover_bonus": int(cover_bonus),
        "missed_penalty": int(missed_penalty),
        "debt_percentage": round(debt_percentage, 2),
        "total_students": int(total_students),
        "total_debtors": int(total_debtors),
        "total_salary": int(total_salary)
    }
