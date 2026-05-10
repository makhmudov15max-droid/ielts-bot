HOURLY_RATES = {
    "nova": 11000,
    "prime": 12000,
    "apex": 13000,
    "leader": 15000,
}


def calculate_admin_salary(data):

    hourly_rate = HOURLY_RATES[data["status"]]

    fixa = (
        data["daily_hours"]
        * data["worked_days"]
        * hourly_rate
    )

    total_salary = fixa

    return {
        "fixa": int(fixa),
        "total_salary": int(total_salary),
    }
