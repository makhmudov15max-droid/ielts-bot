@dp.message_handler(state=AdminSalaryStates.actual_active)
async def get_actual_active(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(actual_active=value)

    await message.answer(
        "Rus tili biladimi? yes/no"
    )

    await AdminSalaryStates.knows_russian.set()


@dp.message_handler(state=AdminSalaryStates.knows_russian)
async def get_russian(message: types.Message, state: FSMContext):

    answer = message.text.lower()

    if answer not in ["yes", "no"]:
        return await message.answer(
            "Faqat yes yoki no yozing"
        )

    await state.update_data(
        knows_russian=answer == "yes"
    )

    await message.answer(
        "IELTS 7+ bormi? yes/no"
    )

    await AdminSalaryStates.has_ielts.set()


@dp.message_handler(state=AdminSalaryStates.has_ielts)
async def get_ielts(message: types.Message, state: FSMContext):

    answer = message.text.lower()

    if answer not in ["yes", "no"]:
        return await message.answer(
            "Faqat yes yoki no yozing"
        )

    await state.update_data(
        has_ielts=answer == "yes"
    )

    await message.answer(
        "Cover hours kiriting:"
    )

    await AdminSalaryStates.cover_hours.set()


@dp.message_handler(state=AdminSalaryStates.cover_hours)
async def get_cover_hours(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(cover_hours=value)

    await message.answer(
        "Missed hours kiriting:"
    )

    await AdminSalaryStates.missed_hours.set()


@dp.message_handler(state=AdminSalaryStates.missed_hours)
async def get_missed_hours(message: types.Message, state: FSMContext):

    try:
        value = float(message.text)
    except:
        return await message.answer(
            "Faqat raqam kiriting"
        )

    await state.update_data(missed_hours=value)

    data = await state.get_data()

    result = calculate_admin_salary(data)

    text = f"""
📊 ADMIN SALARY

🏅 Status: {data['status'].upper()}

💰 Fixa: {result['fixa']:,}

📈 Individual KPI: {result['individual_kpi']}%

📈 Conversion KPI: {result['conversion_kpi']}%

📈 Active KPI: {result['active_kpi']}%

📊 Weighted KPI: {result['weighted_kpi']}%

━━━━━━━━━━━━━━

💵 KPI Rate: {result['bonus_rate']:,}

🎯 Base KPI Bonus: {result['base_kpi_bonus']:,}

🏆 Final KPI Bonus: {result['final_kpi_bonus']:,}

━━━━━━━━━━━━━━

🇷🇺 Russian Bonus: {result['russian_bonus']:,}

🎓 IELTS Bonus: {result['ielts_bonus']:,}

🔄 Cover Bonus: {result['cover_bonus']:,}

📉 Penalty: {result['penalty']:,}

━━━━━━━━━━━━━━
💵 TOTAL: {result['total_salary']:,}
"""

    await message.answer(text)

    await state.finish()
