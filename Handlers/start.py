async def toggle_day_callback(call: types.CallbackQuery, state: FSMContext):
    day_code = call.data.split("_")[1]
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", [])
    
    if day_code in selected_days:
        selected_days.remove(day_code)
    else:
        selected_days.append(day_code)
        
    await state.update_data(selected_days=selected_days)
    await call.message.edit_reply_markup(
        reply_markup=get_inline_days_keyboard(selected_days)
    )
    await call.answer()

@start_router.callback_query(TaskStates.waiting_for_days, F.data == "days_done")
async def days_done_callback(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", [])
    
    if not selected_days:
        await call.answer(text="Iltimos, kamida bitta kun tanlang!", show_alert=True)
        return
        
    await state.update_data(task_days=", ".join(selected_days))
    await call.message.delete()
    await call.message.answer(
        text="How many times per day? (Once or multiple times?)",
        reply_markup=frequency_keyboard
    )
    await state.set_state(TaskStates.waiting_for_frequency)
    await call.answer()
