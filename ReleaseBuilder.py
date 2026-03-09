import os
import json
import hashlib
from datetime import datetime

# ================= CẤU HÌNH =================
SERVER_DIR = "AvServer" # Thư mục chứa file để up lên mạng
LATEST_VERSION = "2.0.0" # Bác đổi số này mỗi khi ra bản mới
DUMMY_FILES_DIR = os.path.join(SERVER_DIR, "heavy_payloads")
# ============================================

def calculate_sha256(filepath):
    """Tính mã Hash SHA-256 siêu tốc bằng cách đọc từng chunk"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Đọc mỗi lần 4MB để không tốn RAM dù file nặng 10GB
        for byte_block in iter(lambda: f.read(4096 * 1024), b""): 
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_dummy_files(target_dir, num_files=4, size_mb=50):
    """Tạo file rác để test tải nặng (Mặc định 4 file x 50MB = 200MB)"""
    os.makedirs(target_dir, exist_ok=True)
    print(f"[*] Dang tao {num_files} file nang, moi file {size_mb}MB. Vui long doi...")
    for i in range(num_files):
        filepath = os.path.join(target_dir, f"database_pack_{i}.dat")
        if not os.path.exists(filepath):
            with open(filepath, "wb") as f:
                f.write(os.urandom(size_mb * 1024 * 1024))
            print(f"  -> Da tao xong: {filepath}")
        else:
            print(f"  -> Da ton tai: {filepath} (Bo qua tao moi)")

def build_release():
    print(f"=== HỆ THỐNG ĐÓNG GÓI PHIÊN BẢN (v{LATEST_VERSION}) ===")
    os.makedirs(SERVER_DIR, exist_ok=True)
    
    # 1. Đẻ file 200MB để test tải
    generate_dummy_files(DUMMY_FILES_DIR)
    
    # 2. Quét file và tính Hash
    manifest_files = []
    print("\n[*] Dang tinh toan ma Hash (SHA-256) cho toan bo file...")
    
    for root, dirs, files in os.walk(SERVER_DIR):
        for file in files:
            # Bỏ qua không tự hash chính các file cấu hình json
            if file in ["update_controller.json", "update_history.json"]:
                continue 
                
            filepath = os.path.join(root, file)
            # Tạo đường dẫn tương đối (VD: heavy_payloads/database_pack_0.dat)
            rel_path = os.path.relpath(filepath, SERVER_DIR).replace("\\", "/") 
            
            file_hash = calculate_sha256(filepath)
            manifest_files.append({
                "path": rel_path,
                "hash": file_hash
            })
            print(f"  -> {rel_path}: {file_hash[:8]}...")

    # 3. Tạo/Cập nhật file JSON cho Client
    release_info = {
        "has_update": True,
        "version": LATEST_VERSION,
        "release_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "manifest": {
            "files": manifest_files
        }
    }
    
    controller_path = os.path.join(SERVER_DIR, "update_controller.json")
    with open(controller_path, "w", encoding="utf-8") as f:
        json.dump(release_info, f, indent=4)
    print(f"\n[+] Da xuat file JSON cho Client: {controller_path}")

    # 4. Lưu lại lịch sử các phiên bản cũ
    history_path = os.path.join(SERVER_DIR, "update_history.json")
    history_data = []
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            history_data = json.load(f)
    
    # Xóa bản ghi trùng nếu bác chạy lại script nhiều lần cho cùng 1 version
    history_data = [item for item in history_data if item["version"] != LATEST_VERSION]
    history_data.append(release_info) # Thêm bản ghi mới nhất vào cuối sổ
    
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=4)
    print(f"[+] Da cap nhat Lich su phien ban: {history_path}")
    print("=== HOAN TAT! BAC CO THE UPLOAD THU MUC 'AvServer' LEN GITHUB ===")

if __name__ == "__main__":
    build_release()