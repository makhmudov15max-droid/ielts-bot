def get_teacher_workload(teacher_name):
    try:
        data = sheet.get_all_values()[1:] # Headerdan keyingi barcha qatorlar
        today = datetime.today()
        
        active_groups = []
        nabor_groups = []
        
        for row in data:
            if len(row) < 10: continue
            
            # C ustuni (index 2) - Teacher
            current_teacher = row[2].strip()
            
            if current_teacher == teacher_name:
                group_id = row[3].strip()     # D ustuni - Nom
                level = row[4].strip()        # E ustuni - Level
                end_date_raw = row[7].strip() # H ustuni - End Date
                status = row[9].strip()       # J ustuni - Status
                
                if not group_id: continue
                
                # Sanani hisoblash
                end_date = parse_date(end_date_raw)
                days_left = (end_date - today).days if end_date else "?"
                
                group_info = {
                    "id": group_id,
                    "level": level,
                    "days": days_left,
                    "status": status
                }
                
                # Nabor yoki aktivligini ajratamiz
                if "Nabor" in status or "Naborga" in status:
                    nabor_groups.append(group_info)
                else:
                    active_groups.append(group_info)

        if not active_groups and not nabor_groups:
            return f"😕 {teacher_name} uchun hozircha guruhlar topilmadi."

        # Xabar matnini yig'ish
        header_text = f"👨‍🏫 <b>{teacher_name}</b> ning {len(active_groups)} ta guruhi hamda {len(nabor_groups)} ta naborda guruhi bor.\n"
        
        details = []
        # Avval aktiv guruhlar
        for g in active_groups:
            details.append(f"🔹 <b>{g['id']}</b> ({g['level']})\n⏳ {g['days']} kun qoldi\n📌 {g['status']}")
            
        # Keyin nabor guruhlar
        if nabor_groups:
            details.append("\n<b>📦 Nabor guruhlar:</b>")
            for g in nabor_groups:
                details.append(f"🔸 <b>{g['id']}</b> ({g['level']})\n📌 {g['status']}")

        return header_text + "\n" + "\n\n".join(details)

    except Exception as e:
        return f"⚠️ Xatolik: {str(e)}"
