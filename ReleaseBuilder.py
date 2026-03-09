import os
import json
import hashlib
import time
from datetime import datetime

# ================= CẤU HÌNH =================
SERVER_DIR = "AvServer" 
LATEST_VERSION = "2.0.0" 
DUMMY_FILES_DIR = os.path.join(SERVER_DIR, "heavy_payloads")
# ============================================

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096 * 1024), b""): 
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_dummy_files(target_dir, num_files=4, size_mb=50):
    os.makedirs(target_dir, exist_ok=True)
    print(f"[*] Dang tao {num_files} file nang, moi file {size_mb}MB...")
    for i in range(num_files):
        filepath = os.path.join(target_dir, f"database_pack_{i}.dat")
        if not os.path.exists(filepath):
            with open(filepath, "wb") as f:
                f.write(os.urandom(size_mb * 1024 * 1024))
            print(f"  -> Da tao: {filepath}")

def build_release():
    print(f"=== HỆ THỐNG ĐÓNG GÓI PHIÊN BẢN (v{LATEST_VERSION}) ===")
    os.makedirs(SERVER_DIR, exist_ok=True)
    generate_dummy_files(DUMMY_FILES_DIR)
    
    manifest_files = []
    print("\n[*] Dang tinh toan ma Hash & Size...")
    
    for root, dirs, files in os.walk(SERVER_DIR):
        for file in files:
            if file in ["update_controller.json", "update_history.json"]:
                continue 
                
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, SERVER_DIR).replace("\\", "/") 
            
            # ===== ĐÁP ỨNG CHÍNH XÁC STRUCT C++ (FileInfo) =====
            manifest_files.append({
                "path": rel_path,
                "url": "",                  # C++ tự nối chuỗi rồi nên cứ để rỗng
                "md5": calculate_sha256(filepath), # Đổi tên từ hash thành md5
                "size": os.path.getsize(filepath), # Thêm field size
                "metadata": {}              # Field metadata là json rỗng
            })
            print(f"  -> {rel_path} (OK)")

    # ===== ĐÁP ỨNG CHÍNH XÁC STRUCT C++ (UpdateCheckResponse & Manifest) =====
    release_info = {
        "has_update": True,
        "manifest": {
            "version": LATEST_VERSION,
            "expires_at": int(time.time()) + 2592000, # Thêm expires_at (30 ngày nữa)
            "files": manifest_files
        }
    }
    
    # Ghi ra file JSON
    controller_path = os.path.join(SERVER_DIR, "update_controller.json")
    with open(controller_path, "w", encoding="utf-8") as f:
        json.dump(release_info, f, indent=4)
    print(f"\n[+] Da xuat file JSON cho Client: {controller_path}")

    # Ghi lịch sử
    history_path = os.path.join(SERVER_DIR, "update_history.json")
    history_data = []
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            history_data = json.load(f)
            
    history_data = [item for item in history_data if item.get("manifest", {}).get("version") != LATEST_VERSION]
    history_data.append(release_info) 
    
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=4)
        
    print("=== HOAN TAT! BAC HAY DAY LEN GITHUB NHÉ ===")

if __name__ == "__main__":
    build_release()