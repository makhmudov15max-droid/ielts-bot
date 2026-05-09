async def calculate_admin_salary(data):

    status = data.get("status")

    rates = {
        "Nova": 11000,
        "Prime": 12000,
        "Apex": 13000,
        "Leader": 15000
    }

    hourly_rate = rates.get(status, 0)

    hours = float(data.get("hours", 0))
    days = float(data.get("days", 0))

    missed_hours = float(data.get("missed_hours", 0))
    cover_hours = float(data.get("cover_hours", 0))

    total_hours = hours * days

    fixa = total_hours * hourly_rate

    penalty = missed_hours * hourly_rate

    cover_bonus = cover_hours * hourly_rate

    russian_bonus = 500000 if data.get("russian") == "✅ Ha" else 0
    ielts_bonus = 1000000 if data.get("ielts") == "✅ Ha" else 0

    individual_plan = float(data.get("individual_plan", 1))
    actual_sales = float(data.get("actual_sales", 0))

    conversion_plan = float(data.get("conversion_plan", 1))
    actual_conversion = float(data.get("actual_conversion", 0))

    active_plan = float(data.get("active_plan", 1))
    actual_active = float(data.get("actual_active", 0))

    individual_percentage = (actual_sales / individual_plan) * 100

    conversion_percentage = (actual_conversion / conversion_plan) * 100

    active_percentage = (actual_active / active_plan) * 100

    weighted_kpi = (
        (individual_percentage * 0.5) +
        (conversion_percentage * 0.3) +
        (active_percentage * 0.2)
    )

    if individual_percentage <= 49:
        bonus_rate = 0
    elif individual_percentage <= 60:
        bonus_rate = 5000
    elif individual_percentage <= 70:
        bonus_rate = 6000
    elif individual_percentage <= 80:
        bonus_rate = 10000
    elif individual_percentage <= 90:
        bonus_rate = 15000
    elif individual_percentage <= 95:
        bonus_rate = 18000
    elif individual_percentage <= 100:
        bonus_rate = 25000
    elif individual_percentage <= 110:
        bonus_rate = 30000
    elif individual_percentage <= 120:
        bonus_rate = 32000
    elif individual_percentage <= 130:
        bonus_rate = 35000
    else:
        bonus_rate = 40000

    base_kpi_bonus = actual_sales * bonus_rate

    kpi_bonus = base_kpi_bonus * (weighted_kpi / 100)

    total_salary = (
        fixa
        - penalty
        + cover_bonus
        + russian_bonus
        + ielts_bonus
        + kpi_bonus
    )

    return {
        "individual_percentage": individual_percentage,
        "conversion_percentage": conversion_percentage,
        "active_percentage": active_percentage,
        "weighted_kpi": weighted_kpi,
        "kpi_bonus": kpi_bonus,
        "cover_bonus": cover_bonus,
        "penalty": penalty,
        "fixa": fixa,
        "russian_bonus": russian_bonus,
        "ielts_bonus": ielts_bonus,
        "total_salary": total_salary
    }
