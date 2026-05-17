# calculators/admin_calc.py

# Rasmga asosan yangilangan bonus stavkalari shkalasi
BONUS_RATES = [
    (0, 49, 0),
    (50, 60, 5000),
    (61, 70, 6000),
    (71, 80, 10000),
    (81, 90, 15000),
    (91, 95, 18000),
    (96, 100, 25000),
    (101, 110, 30000),
    (111, 120, 32000),  
    (121, 130, 35000),
    (131, 9999, 40000),
]

HOURLY_RATES = {
    "nova": 11000,
    "prime": 12000,
    "apex": 13000,
    "leader": 15000,
}

def percent(actual, plan):
    if plan <= 0:
        return 0
    return (actual / plan) * 100

def get_bonus_rate(individual_kpi):
    individual_kpi = round(individual_kpi)
    for min_val, max_val, rate in BONUS_RATES:
        if min_val <= individual_kpi <= max_val:
            return rate
    return 0

def calculate_admin_salary(data: dict) -> dict:
    # Ma'lumotlarni raqamlarga o'tkazish
    status = str(data.get("status", "nova")).lower()
    daily_hours = float(data.get("daily_hours", 0))
    worked_days = float(data.get("worked_days", 0))
    
    individual_plan = float(data.get("individual_plan", 0))
    actual_sales = float(data.get("actual_sales", 0))
    conversion_plan = float(data.get("conversion_plan", 0))
    actual_conversion = float(data.get("actual_conversion", 0))
    active_plan = float(data.get("active_plan", 0))
    actual_active = float(data.get("actual_active", 0))
    
    missed_hours = float(data.get("missed_hours", 0))
    cover_hours = float(data.get("cover_hours", 0))
    
    has_ielts = data.get("has_ielts") in [True, "✅ HA", "HA"]
    knows_russian = data.get("knows_russian") in [True, "✅ HA", "HA"]

    # Fixa hisoblash
    hourly_rate = HOURLY_RATES.get(status, 11000)
    fixa = daily_hours * worked_days * hourly_rate

    # Har bir bo'limning bajarilish foizi
    individual_kpi = percent(actual_sales, individual_plan)
    conversion_kpi = percent(actual_conversion, conversion_plan)
    active_kpi = percent(actual_active, active_plan)

    # 🌟 TO'G'RILANDI: Vaznlar rasmga asosan (50% / 30% / 20%) qilindi
    weighted_kpi = (
        (individual_kpi * 0.5) + 
        (conversion_kpi * 0.3) + 
        (active_kpi * 0.2)
    )

    # 🌟 TO'G'RILANDI: KPI bonusni to'g'ri ko'paytirish mantiqi
    bonus_rate = get_bonus_rate(individual_kpi)
    base_kpi_bonus = actual_sales * bonus_rate  # Sotuvlar soni * bonus stavkasi
    final_kpi_bonus = base_kpi_bonus * (weighted_kpi / 100)  # Umumiy KPI foiziga ko'paytiriladi

    # Bonus va jarimalar
    russian_bonus = 500000 if knows_russian else 0
    ielts_bonus = 1000000 if has_ielts else 0
    cover_bonus = cover_hours * hourly_rate
    penalty = missed_hours * hourly_rate

    # Yakuniy oylik
    total_salary = fixa + final_kpi_bonus + russian_bonus + ielts_bonus + cover_bonus - penalty

    return {
        "fixa": int(fixa),
        "individual_kpi": round(individual_kpi, 1),
        "conversion_kpi": round(conversion_kpi, 1),
        "active_kpi": round(active_kpi, 1),
        "weighted_kpi": round(weighted_kpi, 1),
        "bonus_rate": int(bonus_rate),
        "final_kpi_bonus": int(final_kpi_bonus),
        "russian_bonus": int(russian_bonus),
        "ielts_bonus": int(ielts_bonus),
        "cover_bonus": int(cover_bonus),
        "penalty": int(penalty),
        "total_salary": int(total_salary)
    }
