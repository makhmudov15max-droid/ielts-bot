def calculate_weighted_kpi(individual, conversion, active):
    return (
        individual * 0.4 +
        conversion * 0.3 +
        active * 0.3
    )


def calculate_admin_salary(data):
    weighted_kpi = calculate_weighted_kpi(
        data["individual_kpi"],
        data["conversion_kpi"],
        data["active_kpi"]
    )

    kpi_bonus = data["fixed_salary"] * (weighted_kpi / 100)

    final_salary = (
        data["fixed_salary"]
        + kpi_bonus
        + data["bonus"]
        - data["penalty"]
    )

    return {
        "weighted_kpi": round(weighted_kpi, 1),
        "kpi_bonus": int(kpi_bonus),
        "final_salary": int(final_salary)
    }
