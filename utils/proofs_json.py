import json
import os
from datetime import datetime

PROOFS_FILE = "proofs.json"


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


def add_proof(user_id, user_name, task_id, task_name, task_description, proof_type, file_id, group_chat_id):
    """Yangi isbot qo'shish"""
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
        "proof_type": proof_type,  # "Photo" yoki "Video message"
        "file_id": file_id,
        "group_chat_id": group_chat_id,
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S")
    }
    
    proofs.append(new_proof)
    save_proofs(proofs)
    return new_proof


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
    
    users = load_users(ADMIN_ID)
    result = []
    
    # Role dagi barcha user larni topish
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
