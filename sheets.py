def get_report(days_limit):
    try:
        data = sheet.get_all_values()[1:] 
        today = datetime.today()
        result = []
        
        # DEBUG: Bot hozirgi vaqtni qanday ko'rayotganini tekshiramiz
        print(f"DEBUG: Today is {today}")

        for row in data:
            if len(row) < 8: continue
            
            teacher = row[2].strip()      
            group_id = row[3].strip()     
            level = row[4].strip()        
            end_date_raw = row[7].strip() 

            if not group_id or not end_date_raw: continue

            # FILTRNI YUMSHATAMIZ (Katta-kichik harfga qaramaydi)
            if "IELTS" not in level.upper():
                continue

            end_date = parse_date(end_date_raw)
            if not end_date: continue

            # Farqni hisoblaymiz
            diff = (end_date - today).days
            
            # DEBUG: Sardorbekning guruhini ko'rganda nima bo'layotganini log qilamiz
            if "114" in group_id:
                print(f"DEBUG: Group 114 found! End: {end_date}, Diff: {diff}")

            # Shartni kengaytiramiz: tugagan bo'lsa ham ko'rsatsin (-5 kundan 30 kungacha)
            if -5 <= diff <= days_limit:
                emoji = "🔴" if diff <= 14 else "🟡"
                if diff < 0: emoji = "❌" # Muddat o'tib ketgan bo'lsa
                
                res = f"{emoji} <b>{group_id}</b>\n⏳ {diff} kun qoldi\n👨‍🏫 {teacher}"
                result.append(res)

        if not result:
            return f"📊 Topilmadi. Bot vaqti: {today.strftime('%d.%m.%Y')}"

        return f"📊 MONITORING\n\n" + "\n\n".join(result)
    except Exception as e:
        return f"⚠️ Xato: {str(e)}"
