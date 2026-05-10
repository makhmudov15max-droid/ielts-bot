HOURLY_RATES = {
    "nova": 11000,
    "prime": 12000,
    "apex": 13000,
    "leader": 15000,
}


def percent(actual, plan):

    if plan == 0:
        return 0

    return (actual / plan) * 100


def calculate_admin_salary(data):

    hourly_rate = HOURLY_RATES[data["status"]]

    fixa = (
        data["daily_hours"]
        * data["worked_days"]
        * hourly_rate
    )

    individual_kpi = percent(
        data["actual_sales"],
        data["individual_plan"]
    )

    conversion_kpi = percent(
        data["actual_conversion"],
        data["conversion_plan"]
    )

    active_kpi = percent(
        data["actual_active"],
        data["active_plan"]
    )

    weighted_kpi = (
        individual_kpi * 0.5
        + conversion_kpi * 0.3
        + active_kpi * 0.2
    )

    total_salary = fixa

    return {
        "fixa": int(fixa),

        "individual_kpi": round(individual_kpi, 1),

        "conversion_kpi": round(conversion_kpi, 1),

        "active_kpi": round(active_kpi, 1),

        "weighted_kpi": round(weighted_kpi, 1),

        "total_salary": int(total_salary),
    }
