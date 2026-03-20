import os
import json
import hashlib
import time
from datetime import datetime

# ================= CẤU HÌNH =================
SERVER_DIR = "AvServer" 
# ============================================

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096 * 1024), b""): 
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_auto_version():
    return datetime.now().strftime("2.0.%Y%m%d.%H%M%S")

def build_release():
    LATEST_VERSION = get_auto_version()
    print(f"=== HỆ THỐNG TỰ ĐỘNG ĐÓNG GÓI PHIÊN BẢN (v{LATEST_VERSION}) ===")
    
    os.makedirs(SERVER_DIR, exist_ok=True)
    
    # =====================================================================
    # [MA THUẬT ĐÁNH LỪA C++]: Ép ghi nội dung mới vào version.txt
    # Để C++ thấy Hash thay đổi và bắt buộc phải tải Update!
    # =====================================================================
    with open(os.path.join(SERVER_DIR, "version.txt"), "w", encoding="utf-8") as f:
        f.write(f"Phiên bản: {LATEST_VERSION}\nCập nhật lúc: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    manifest_files = []
    print("\n[*] Đang tính toán mã SHA-256 & Size...")
    
    for root, dirs, files in os.walk(SERVER_DIR):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'heavy_payloads']]
        
        for file in files:
            if file in ["update_controller.json", "update_history.json"] or file.endswith('.py') or file.endswith('.pyc'):
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

    manifest_files.sort(key=lambda x: x['path'])

    release_info = {
        "has_update": True,
        "manifest": {
            "version": LATEST_VERSION,
            "expires_at": int(time.time()) + 2592000, 
            "files": manifest_files
        }
    }
    
    controller_path = os.path.join(SERVER_DIR, "update_controller.json")
    with open(controller_path, "w", encoding="utf-8") as f:
        json.dump(release_info, f, indent=4)
    print(f"\n[+] Đã xuất file JSON cho Client: {controller_path}")

    history_path = os.path.join(SERVER_DIR, "update_history.json")
    history_data = []
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            try:
                history_data = json.load(f)
            except json.JSONDecodeError:
                history_data = [] 
            
    history_data = [item for item in history_data if item.get("manifest", {}).get("version") != LATEST_VERSION]
    history_data.append(release_info) 
    
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=4)
        
    print(f"=== HOÀN TẤT BUILD v{LATEST_VERSION}! BÁC HÃY ĐẨY LÊN GITHUB NHÉ ===")

if __name__ == "__main__":
    build_release()