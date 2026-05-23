import json
import os
from datetime import datetime, timedelta, timezone


# ================= FILE PATH =================
PROOFS_FILE = "proofs.json"


# ================= LOAD & SAVE FUNCTIONS =================
def load_proofs():
    """proofs.json faylidan barcha isbotlarni yuklaydi"""
    try:
        if os.path.exists(PROOFS_FILE):
            with open(PROOFS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ Proofs yuklash xatosi: {e}")
    return []


def save_proofs(proofs_database):
    """proofs.json faylga isbotlarni saqlaydi"""
    try:
        with open(PROOFS_FILE, "w", encoding="utf-8") as f:
            json.dump(proofs_database, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Proofs saqlash xatosi: {e}")


# ================= ADD & CLEAN FUNCTIONS =================
def add_proof(user_id, user_name, task_id, task_name, task_description, proof_type, file_id, group_chat_id, text_content=None):
    """Yangi isbot qo'shish va 60 kundan eskilarni o'chirish"""
    proofs = load_proofs()
    
    tashkent_tz = timezone(timedelta(hours=5))
    now = datetime.now(tashkent_tz)
    
    new_proof = {
        "id": len(proofs) + 1,
        "user_id": str(user_id),
        "user_name": user_name,
        "task_id": task_id,
        "task_name": task_name,
        "task_description": task_description,
        "proof_type": proof_type,
        "file_id": file_id if file_id else "",
        "text_content": text_content if text_content else "",
        "group_chat_id": group_chat_id,
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S")
    }
    
    proofs.append(new_proof)
    
    # 60 kundan eski isbotlarni o'chirish
    cutoff = now - timedelta(days=60)
    new_proofs = []
    for p in proofs:
        p_date = datetime.fromisoformat(p["timestamp"])
        if p_date > cutoff:
            new_proofs.append(p)
    
    if len(new_proofs) != len(proofs):
        print(f"🗑 {len(proofs) - len(new_proofs)} ta eski isbot o'chirildi (60 kundan eski)")
        proofs = new_proofs
        for idx, p in enumerate(proofs, 1):
            p["id"] = idx
    
    save_proofs(proofs)
    return new_proof


def clean_old_proofs(days=60):
    """60 kundan eski isbotlarni o'chirish"""
    proofs = load_proofs()
    tashkent_tz = timezone(timedelta(hours=5))
    now = datetime.now(tashkent_tz)
    cutoff = now - timedelta(days=days)
    
    new_proofs = []
    for proof in proofs:
        proof_date = datetime.fromisoformat(proof["timestamp"])
        if proof_date > cutoff:
            new_proofs.append(proof)
    
    if len(new_proofs) != len(proofs):
        save_proofs(new_proofs)
        print(f"🗑 {len(proofs) - len(new_proofs)} ta eski isbot o'chirildi")
    
    return new_proofs


# ================= GET PROOFS BY FILTERS =================
def get_proofs_by_user(user_id, start_date=None, end_date=None):
    """Foydalanuvchi bo'yicha isbotlarni olish"""
    proofs = load_proofs()
    result = []
    
    for proof in proofs:
        if proof["user_id"] == str(user_id):
            if start_date and end_date:
                proof_date = proof["date"]
                if start_date <= proof_date <= end_date:
                    result.append(proof)
            else:
                result.append(proof)
    
    return result


def get_proofs_by_role(role_name, start_date=None, end_date=None):
    """Role bo'yicha isbotlarni olish"""
    from utils.users_json import load_users
    
    users = load_users(6500594896)
    result = []
    
    user_ids = []
    for u_id, u_info in users.items():
        if u_info.get("role") == role_name and u_info.get("name"):
            user_ids.append(u_id)
    
    proofs = load_proofs()
    for proof in proofs:
        if proof["user_id"] in user_ids:
            if start_date and end_date:
                proof_date = proof["date"]
                if start_date <= proof_date <= end_date:
                    result.append(proof)
            else:
                result.append(proof)
    
    return result


def get_proofs_by_date_range(start_date, end_date):
    """Sana oralig'i bo'yicha isbotlarni olish"""
    proofs = load_proofs()
    result = []
    
    for proof in proofs:
        proof_date = proof["date"]
        if start_date <= proof_date <= end_date:
            result.append(proof)
    
    return result
