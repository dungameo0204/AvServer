import os
import json
import hashlib
import time
from datetime import datetime

# ================= CẤU HÌNH =================
SERVER_DIR = "AvServer" 
DUMMY_FILES_DIR = os.path.join(SERVER_DIR, "heavy_payloads")
# ============================================

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096 * 1024), b""): 
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# 1. TỰ ĐỘNG SINH DỮ LIỆU MỚI TINH ĐỂ ĐỔI HASH
def generate_dummy_files(target_dir, num_files=12, size_mb=1): 
    os.makedirs(target_dir, exist_ok=True)
    print(f"[*] Dang tao MOI {num_files} file nang, moi file {size_mb}MB (Mat chut thoi gian)...")
    
    for i in range(num_files):
        filepath = os.path.join(target_dir, f"database_pack_{i}.dat")
        with open(filepath, "wb") as f:
            f.write(os.urandom(size_mb * 1024 * 1024))
        print(f"  -> Da thay mau file: {filepath}")

# 2. TỰ ĐỘNG TĂNG VERSION THEO THỜI GIAN THỰC
def get_auto_version():
    return datetime.now().strftime("2.0.%Y%m%d.%H%M%S")

def build_release():
    LATEST_VERSION = get_auto_version()
    print(f"=== HỆ THỐNG TỰ ĐỘNG ĐÓNG GÓI PHIÊN BẢN (v{LATEST_VERSION}) ===")
    
    os.makedirs(SERVER_DIR, exist_ok=True)
    generate_dummy_files(DUMMY_FILES_DIR)
    
    manifest_files = []
    print("\n[*] Dang tinh toan ma SHA-256 & Size...")
    
    for root, dirs, files in os.walk(SERVER_DIR):
        # =====================================================================
        # [MA THUẬT] CẮT ĐỨT ĐƯỜNG ĐI VÀO THƯ MỤC RÁC TỪ TRONG TRỨNG NƯỚC
        # =====================================================================
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file in ["update_controller.json", "update_history.json"]:
                continue 
                
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, SERVER_DIR).replace("\\", "/") 
            
            manifest_files.append({
                "path": rel_path,
                "url": "",
                "md5": calculate_sha256(filepath), 
                "size": os.path.getsize(filepath),
                "metadata": {}
            })
            print(f"  -> {rel_path} (OK)")

    # Sắp xếp lại danh sách theo bảng chữ cái cho đẹp mắt dễ nhìn
    manifest_files.sort(key=lambda x: x['path'])

    release_info = {
        "has_update": True,
        "manifest": {
            "version": LATEST_VERSION,
            "expires_at": int(time.time()) + 2592000, 
            "files": manifest_files
        }
    }
    
    # Ghi file JSON
    controller_path = os.path.join(SERVER_DIR, "update_controller.json")
    with open(controller_path, "w", encoding="utf-8") as f:
        json.dump(release_info, f, indent=4)
    print(f"\n[+] Da xuat file JSON cho Client: {controller_path}")

    # Ghi lịch sử
    history_path = os.path.join(SERVER_DIR, "update_history.json")
    history_data = []
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            try:
                history_data = json.load(f)
            except json.JSONDecodeError:
                history_data = [] # Chống crash nếu file cũ bị lỗi format
            
    history_data = [item for item in history_data if item.get("manifest", {}).get("version") != LATEST_VERSION]
    history_data.append(release_info) 
    
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=4)
        
    print(f"=== HOAN TAT BUILD v{LATEST_VERSION}! BAC HAY DAY LEN GITHUB NHÉ ===")

if __name__ == "__main__":
    build_release()