HOURLY_RATES = {
    "nova": 11000,
    "prime": 12000,
    "apex": 13000,
    "leader": 15000,
}


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


# ================= KPI PERCENT =================

def percent(actual, plan):

    if plan <= 0:

        return 0

    return (actual / plan) * 100


# ================= BONUS RATE =================

def get_bonus_rate(individual_kpi):

    individual_kpi = round(
        individual_kpi
    )

    for min_val, max_val, rate in BONUS_RATES:

        if min_val <= individual_kpi <= max_val:

            return rate

    return 0


# ================= MAIN CALCULATOR =================

def calculate_admin_salary(data):

    status = data["status"]

    daily_hours = float(
        data["daily_hours"]
    )

    worked_days = float(
        data["worked_days"]
    )

    hourly_rate = HOURLY_RATES[
        status
    ]

    # ================= FIXA =================

    fixa = (
        daily_hours
        * worked_days
        * hourly_rate
    )

    # ================= KPI =================

    individual_kpi = percent(
        float(data["actual_sales"]),
        float(data["individual_plan"])
    )

    conversion_kpi = percent(
        float(data["actual_conversion"]),
        float(data["conversion_plan"])
    )

    active_kpi = percent(
        float(data["actual_active"]),
        float(data["active_plan"])
    )

    # ================= WEIGHTED KPI =================

    weighted_kpi = (

        individual_kpi * 0.5 +

        conversion_kpi * 0.3 +

        active_kpi * 0.2
    )

    # ================= BONUS =================

    bonus_rate = get_bonus_rate(
        individual_kpi
    )

    base_kpi_bonus = (

        float(data["actual_sales"])

        * bonus_rate
    )

    final_kpi_bonus = (

        base_kpi_bonus

        * (weighted_kpi / 100)
    )

    # ================= EXTRAS =================

    russian_bonus = (
        500000
        if data["knows_russian"]
        else 0
    )

    ielts_bonus = (
        1000000
        if data["has_ielts"]
        else 0
    )

    cover_bonus = (

        float(data["cover_hours"])

        * hourly_rate
    )

    penalty = (

        float(data["missed_hours"])

        * hourly_rate
    )

    # ================= TOTAL =================

    total_salary = (

        fixa

        + final_kpi_bonus

        + russian_bonus

        + ielts_bonus

        + cover_bonus

        - penalty
    )

    # ================= RETURN =================

    return {

        "fixa": int(fixa),

        "individual_kpi": round(
            individual_kpi,
            1
        ),

        "conversion_kpi": round(
            conversion_kpi,
            1
        ),

        "active_kpi": round(
            active_kpi,
            1
        ),

        "weighted_kpi": round(
            weighted_kpi,
            1
        ),

        "bonus_rate": int(
            bonus_rate
        ),

        "base_kpi_bonus": int(
            base_kpi_bonus
        ),

        "final_kpi_bonus": int(
            final_kpi_bonus
        ),

        "russian_bonus": int(
            russian_bonus
        ),

        "ielts_bonus": int(
            ielts_bonus
        ),

        "cover_bonus": int(
            cover_bonus
        ),

        "penalty": int(
            penalty
        ),

        "total_salary": int(
            total_salary
        ),
    }
