# Bonus & Jarima Tizimi — Texnik Spetsifikatsiya

## 1. Yangi DB jadvallar

### fines_tariffs (Owner belgilagan tariflar)
| ustun | turi | izoh |
|---|---|---|
| id | SERIAL PK | |
| role | TEXT | qaysi rol uchun (Admin, Kassir...) |
| min_minutes | INTEGER | interval boshi (masalan 1) |
| max_minutes | INTEGER | interval oxiri (masalan 5) |
| amount | INTEGER | shu interval uchun jarima summasi (UZS) |

### fines (har bir jarima yozuvi)
| ustun | turi | izoh |
|---|---|---|
| id | SERIAL PK | |
| user_id | TEXT | |
| user_name | TEXT | |
| role | TEXT | jarima qo'yilgandagi rol |
| date | TEXT | YYYY-MM-DD |
| late_minutes | INTEGER | kechikish daqiqasi (ishga chiqmaganlikda 0) |
| amount | INTEGER | jarima summasi |
| reason | TEXT | 'late' (kechikish) yoki 'absent' (ishga chiqmadi) |
| status | TEXT | 'active' (amalda) yoki 'cancelled' (bekor qilingan) |
| created_at | TIMESTAMP | |
| cancelled_at | TIMESTAMP | |

---

## 2. Logika

### A. Kechikish (xodim "Ishga keldim" bossa, o'sha zahoti)
1. `late_minutes = arrived - work_start` (avvalgi tizimda allaqachon hisoblanadi)
2. Agar `late_minutes > 0`:
   - Xodim roliga mos tarif topiladi (`fines_tariffs` dan)
   - Tarif bo'lmasa → eski tizim (jarima qo'yilmaydi, xabar kelmaydi)
   - Tarif bo'lsa → `fines` ga yozuv qo'shiladi (status='active')
   - Xodimga: "Assalomu alaykum, {ism}. Bugun ishga {X} daqiqa kech kelganingiz aniqlandi. Shu sababli sizga {Y} so'm jarima belgilanadi. Iltimos, kelajakda ish jadvaliga rioya qiling."
   - Owner'ga: ⚠️ Kechikish xabari + jarima summasi + "✏️ Qisqartirish"/"🗑 Bekor qilish" inline tugmalar
3. "Ishga keldim" o'z vaqtida (0 daqiqa):
   - Admin bo'lsa → "100,000 bonusga oz qoldi" xabari (har ish kunida, yakshanba/bayram emas)

### B. Ishga chiqmaganlik (smena yakunida, work_end da)
- Kun oxirida `work_end` dan keyin, agar xodim 'missed' bo'lsa (mavjud `mark_missed_for_date`):
  - Ish kuni bo'lsa (yakshanba/bayram emas)
  - Owner'ga "Ishga kelmadi" xabari + "✏️ Qisqartirish"/"🗑 Bekor qilish" tugmalar
  - Owner istalgan summa kiritadi/bekor qiladi
  - Jarima bossa → `fines` ga yozuv (reason='absent', amount=owner kiritgan)
  - Xodimga C-xabari: "Assalomu alaykum, {ism}. Sizni bugungi ishga kelmaganingiz sababli jarima belgilandi. Iltimos, kelajakda ish jadvaliga rioya qiling."
  - Jarima qo'yilsa → Admin bonus yo'qoladi

### C. Qisqartirish / Bekor qilish (owner inline tugmalar)
- Owner tanlanganda:
  - "✏️ Qisqartirish" → Owner istalgan summa kiritadi → `fines.amount` yangilanadi, status='active'
    - Xodimga A-xabari: "Assalomu alaykum, {ism}. Sizga jarima belgilangandi, biroq ma'muriyat tomonidan qayta ko'rib chiqilib, miqdori {Y} so'mga o'zgartirildi."
  - "🗑 Bekor qilish" → `fines.status='cancelled'`
    - Xodimga B-xabari: "Assalomu alaykum, {ism}. Sizga belgilangan jarima ma'muriyat tomonidan bekor qilindi. E'tiboringiz uchun rahmat."

---

## 3. Xodim paneli (asosiy menyu)

### Yangi tugmalar
- **Admin** roli → "Bonus/Jarima" tugmasi (asosiy menyuda)
- **Boshqa rol** → "jarimalarim" tugmasi (asosiy menyuda)
- (Owner boshqa panelga ega, quyida)

### Flow
1. Bosiladi → 2 oy ro'yxati: joriy oy + o'tgan oy (masalan "Iyul 2026" / "Avgust 2026")
2. Oy tanlanadi →
   - **Admin**, butun oy jarimasiz + ishga chiqmasa:
     - "Bonus: Tabriklaymiz 🙃 100,000 UZS / Jarima: 0 UZS 😎"
   - **Admin**, jarima bo'lsa:
     - "Bonus💰: 0 UZS / Jarima: {X} UZS" + "Kechikishlar" tugmasi
     - "Kechikishlar" bosilsa → sanalar + har birida jarima (shu jumladan bekor qilinganlar "bekor qilindi" deb)
   - **Boshqa rol**:
     - "Jarimalarim: {X} UZS" (bonus haqida hech narsa)
     - Kechikishlar bo'lsa, "Kechikishlar" tugmasi ham chiqadi (barcha rol uchun)

### Bonus hisobi
- Bonus faqat **Admin** uchun, har oy 100,000 (mustaqil)
- Shart: butun oy bitta ham 'active' jarima bo'lmasa (kechikish ham, ishga chiqmaganlik ham qo'yilgan bo'lmasa) → bonus bor
- Bonus oy yakunida (oxirgi ish kuni) avtomatik xabar + panelda ko'rinadi
- Bekor qilingan jarima bonusni qaytarmaydi (biror marta jarima qo'yilgan bo'lsa → o'sha oy bonus yo'q)

---

## 4. Owner paneli (asosiy menyu)

### Yangi tugma: "Bonus&Jarima"
1. Bosiladi → rol tanlash (Admin, Kassir, Sanitar, Manager...)
2. Rol tanlanadi →
   - **Admin**: xodimlar ro'yxati (adminlar) + bonus haqida ma'lumot bo'ladi
   - **Boshqa rol**: xodimlar ro'yxati, faqat jarima ma'lumoti
3. Xodim tanlanadi → 6 oylik ro'yxat (joriy + 5 o'tgan)
4. Oy tanlanadi →
   - O'sha oyda kechikkan/chiqmagan sanalar + jarimalari (har biri uchun "🗑 Bekor qilish" imkoniyati bo'lishi mumkin)
   - Yakunida umumiy jarima / yoki bonus (Admin, jarimasiz bo'lsa) / yoki "bu oyda umuman kech qolmadilar, 100,000 bonusga ega bo'ldilar"
   - Boshqa rol (Admin emas) jarimasiz bo'lsa → bonus ko'rinmaydi, "jarima yo'q" deyiladi

### Sozlamalar → yangi "Jarimalar" tugmasi
1. Bosiladi → barcha rol ro'yxati
2. Rol tanlanadi → hozirgi tariflar ko'rsatiladi + intervallarni o'zgartirish
3. Ketma-ket so'rov (A variant):
   - "1-5 daqiqa uchun jarima summasini kiriting" → Owner summa
   - "6-15 daqiqa uchun jarima summasini kiriting" → ...
   - Owner o'zi intervallarni qo'shishi/olib tashlashi mumkin (standart 1-5, 6-15, 16-30)
   - Ishlari tugagach "Tayyor" deb bosadi
4. Tariflar `fines_tariffs` jadvaliga saqlanadi

---

## 5. Xabarlar matnlari (rasmiy, sayqallangan)

- **Kechikish (xodimga):** "Assalomu alaykum, {ism}. Bugun ishga {X} daqiqa kech kelganingiz aniqlandi. Shu sababli sizga {Y} so'm jarima belgilanadi. Iltimos, kelajakda ish jadvaliga rioya qiling."
- **Ishga chiqmadi (owner'ga):** "⚠️ Ishga kelmadi. {Ism} bugun ishga kelmadi. Sababi: ... / Jarima belgilash tugmasi"
- **Ishga chiqmasa (xodimga C):** "Assalomu alaykum, {ism}. Sizni bugungi ishga kelmaganingiz sababli jarima belgilandi. Iltimos, kelajakda ish jadvaliga rioya qiling."
- **Qisqartirilganda (xodimga A):** "Assalomu alaykum, {ism}. Sizga jarima belgilangandi, biroq ma'muriyat tomonidan qayta ko'rib chiqilib, miqdori {Y} so'mga o'zgartirildi."
- **Bekor qilinganda (xodimga B):** "Assalomu alaykum, {ism}. Sizga belgilangan jarima ma'muriyat tomonidan bekor qilindi. E'tiboringiz uchun rahmat."
- **Bonus (panelda):** "Tabriklaymiz 🙃 100,000 UZS"
- **Bonusga oz qoldi (har ish kunida):** "...100,000 bonusga oz qoldi"
- **Oy yakunida bonus:** "Tabriklaymiz {ism}! Bu oy hech qachon kech kelmadingiz. Sizga 100,000 so'm bonus berildi. 🎉"
