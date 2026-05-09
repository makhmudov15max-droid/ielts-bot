async def calculate_cashier_salary(data):

    hours = float(data.get("hours", 0))

    days = float(data.get("days", 0))

    missed_days = float(data.get("missed_days", 0))

    cover_days = float(data.get("cover_days", 0))

    active_students = float(data.get("active_students", 0))

    active_debtors = float(data.get("active_debtors", 0))

    archive_students = float(data.get("archive_students", 0))

    archive_debtors = float(data.get("archive_debtors", 0))


    if hours <= 8:

        daily_salary = hours * 15000

    else:

        extra_hours = hours - 8

        daily_salary = (8 * 15000) + (extra_hours * 20000)


    worked_salary = daily_salary * days


    missed_penalty = missed_days * 15000

    cover_bonus = cover_days * 15000


    total_students = active_students + archive_students

    total_debtors = active_debtors + archive_debtors


    debt_percentage = (
        total_debtors * 100 / total_students
    )


    if debt_percentage == 0:

        multiplier = 2.5

    elif debt_percentage <= 2:

        multiplier = 2.0

    elif debt_percentage <= 5:

        multiplier = 1.8

    elif debt_percentage <= 7:

        multiplier = 1.7

    elif debt_percentage <= 10:

        multiplier = 1.6

    elif debt_percentage <= 15:

        multiplier = 1.5

    elif debt_percentage <= 20:

        multiplier = 1.4

    elif debt_percentage <= 30:

        multiplier = 1.2

    else:

        multiplier = 1.0


    multiplied_salary = worked_salary * multiplier


    final_salary = (
        multiplied_salary
        + cover_bonus
        - missed_penalty
    )


    return {

        "daily_salary": daily_salary,

        "worked_salary": worked_salary,

        "missed_penalty": missed_penalty,

        "cover_bonus": cover_bonus,

        "debt_percentage": debt_percentage,

        "multiplier": multiplier,

        "final_salary": final_salary
    }
