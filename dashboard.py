from flask import Flask, render_template_string, jsonify, request
import subprocess
import os

app = Flask(__name__)

# Thư mục gốc chứa server
BASE_DIR = os.path.abspath('.')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AvServer Manager Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; display: flex; justify-content: center; padding: 30px 0;}
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 700px; }
        h2 { color: #333; margin-top: 0; text-align: center; }
        h3 { color: #555; text-align: left; border-bottom: 2px solid #eee; padding-bottom: 5px; margin-top: 25px; display: flex; justify-content: space-between; align-items: center;}
        
        /* Buttons */
        .btn-main { width: 100%; padding: 15px; margin: 10px 0; font-size: 16px; font-weight: bold; border: none; border-radius: 5px; cursor: pointer; color: white; transition: 0.3s; }
        /* Nút Deploy Gộp 2 Trong 1 */
        .btn-deploy { background-color: #FF5722; box-shadow: 0 4px 6px rgba(255,87,34,0.3); }
        .btn-deploy:hover { background-color: #E64A19; transform: translateY(-1px); }
        .btn-deploy:active { transform: translateY(1px); }
        
        /* Micro Buttons for Tree */
        .btn-sm { padding: 3px 8px; font-size: 12px; border: none; border-radius: 3px; cursor: pointer; color: white; font-weight: bold; }
        .bg-blue { background: #0078D7; }
        .bg-blue:hover { background: #005A9E; }
        .bg-red { background: #dc3545; }
        .bg-red:hover { background: #c82333; }
        
        /* Tree View Styles */
        .tree-box { max-height: 350px; overflow-y: auto; background: #fafafa; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
        ul.tree { list-style: none; padding-left: 20px; margin: 0; text-align: left; }
        ul.tree-root { padding-left: 0; }
        ul.tree li { margin: 2px 0; }
        summary { cursor: pointer; font-weight: bold; background: #e9ecef; padding: 8px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; user-select: none; }
        summary:hover { background: #dee2e6; }
        
        .file-item { display: flex; justify-content: space-between; align-items: center; padding: 6px 8px; border-bottom: 1px dashed #ddd; background: white;}
        .file-item:hover { background: #f8f9fa; }
        
        /* Log Terminal */
        .log-box { background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 5px; text-align: left; height: 180px; overflow-y: auto; font-family: monospace; font-size: 13px; margin-top: 20px; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container">
        <h2>☁️ Server Management Dashboard</h2>
        
        <input type="file" id="fileUpload" style="display:none" onchange="doUpload()">
        
        <div class="file-manager">
            <h3>
                <span>📂 File Explorer (Workspace)</span>
                <button class="btn-sm bg-blue" onclick="prepareUpload('.')">📤 Thêm file vào Root</button>
            </h3>
            <div class="tree-box" id="treeContainer">
                </div>
        </div>

        <h3>⚡ Actions</h3>
        <button id="deployBtn" class="btn-main btn-deploy" onclick="autoDeploy()">🚀 ONE-CLICK DEPLOY (BUILD & PUSH)</button>
        
        <div class="log-box" id="terminal">System Ready...\n</div>
    </div>

    <script>
        let targetFolder = '';

        window.onload = loadTree;
        const terminal = document.getElementById('terminal');
        const deployBtn = document.getElementById('deployBtn');

        function logToTerminal(msg, type="info") {
            let prefix = type === "error" ? "[ERROR] " : type === "success" ? "[SUCCESS] " : "[INFO] ";
            terminal.innerHTML += prefix + msg + "\\n";
            terminal.scrollTop = terminal.scrollHeight;
        }

        function loadTree() {
            fetch('/api/tree?t=' + Date.now(), { cache: 'no-store' })
                .then(res => res.text())
                .then(html => {
                    document.getElementById('treeContainer').innerHTML = html;
                });
        }

        function prepareUpload(folderPath) {
            targetFolder = folderPath;
            document.getElementById('fileUpload').click();
        }

        function doUpload() {
            const fileInput = document.getElementById('fileUpload');
            if(fileInput.files.length === 0) return;
            
            const formData = new FormData();
            formData.append("file", fileInput.files[0]);
            formData.append("folder", targetFolder);

            logToTerminal("Đang tải file lên thư mục: " + (targetFolder === '.' ? 'Root' : targetFolder), "info");
            fetch('/upload', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    if(data.status === 'success') {
                        logToTerminal(data.message, "success");
                        fileInput.value = ""; 
                        loadTree(); 
                    } else {
                        logToTerminal(data.message, "error");
                    }
                });
        }

        function deleteFile(filePath) {
            if(!confirm(`Xóa file này: ${filePath}?`)) return;
            
            fetch('/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: filePath })
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === 'success') {
                    logToTerminal(data.message, "success");
                    loadTree();
                } else {
                    logToTerminal(data.message, "error");
                }
            });
        }

        // ==========================================
        // HÀM MỚI: GỘP BUILD VÀ PUSH VÀO MỘT LUỒNG
        // ==========================================
        async function autoDeploy() {
            deployBtn.disabled = true;
            deployBtn.innerText = "⏳ ĐANG XỬ LÝ (XIN CHỜ VÀI GIÂY)...";
            deployBtn.style.backgroundColor = "gray";

            try {
                // Bước 1: Gọi Build Manifest
                logToTerminal("--- BƯỚC 1: ĐÓNG GÓI PHIÊN BẢN (BUILD) ---", "info");
                let buildRes = await fetch('/build?t=' + Date.now(), { cache: 'no-store' });
                let buildData = await buildRes.json();
                
                if (buildData.status === 'success') {
                    logToTerminal(buildData.message, "success");
                    loadTree(); // Cập nhật lại list file để thấy JSON mới
                    
                    // Bước 2: Gọi Push Git
                    logToTerminal("--- BƯỚC 2: ĐẨY LÊN GITHUB (PUSH) ---", "info");
                    let pushRes = await fetch('/push?t=' + Date.now(), { cache: 'no-store' });
                    let pushData = await pushRes.json();

                    if (pushData.status === 'success') {
                        logToTerminal(pushData.message, "success");
                        logToTerminal("🎉 HOÀN TẤT! HỆ THỐNG ĐÃ CẬP NHẬT. (Đợi 3-5 phút để CDN đồng bộ)", "success");
                    } else {
                        logToTerminal(pushData.message, "error");
                    }
                } else {
                    logToTerminal(buildData.message, "error");
                    logToTerminal("Hủy Push do lỗi Build!", "error");
                }
            } catch (err) {
                logToTerminal("Lỗi kết nối Server: " + err.message, "error");
            } finally {
                // Khôi phục nút
                deployBtn.disabled = false;
                deployBtn.innerText = "🚀 ONE-CLICK DEPLOY (BUILD & PUSH)";
                deployBtn.style.backgroundColor = ""; 
            }
        }
    </script>
</body>
</html>
"""

# Hàm đệ quy quét thư mục
def build_tree_html(current_dir, is_root=False):
    html = '<ul class="tree tree-root">' if is_root else '<ul class="tree">'
    try:
        items = sorted(os.listdir(current_dir), key=lambda x: (not os.path.isdir(os.path.join(current_dir, x)), x.lower()))
    except Exception:
        return "</ul>"
        
    for item in items:
        if item in ['.git', '.vs', '__pycache__', '.vscode', 'venv']: continue
        
        full_path = os.path.join(current_dir, item)
        rel_path = os.path.relpath(full_path, BASE_DIR).replace('\\', '/')
        
        if os.path.isdir(full_path):
            html += f'''
            <li>
                <details>
                    <summary>
                        <span>📁 {item}</span>
                        <button class="btn-sm bg-blue" onclick="prepareUpload('{rel_path}')">📤 Thêm file</button>
                    </summary>
                    {build_tree_html(full_path)}
                </details>
            </li>
            '''
        else:
            delete_btn = f'<button class="btn-sm bg-red" onclick="deleteFile(\'{rel_path}\')">🗑️ Xóa</button>'
            if item.endswith('.py') or item == 'README.md':
                delete_btn = '<span style="color:gray; font-size:12px;">🔒 Khóa</span>'
                
            html += f'<li><div class="file-item"><span>📄 {item}</span> {delete_btn}</div></li>'
            
    html += '</ul>'
    return html

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/tree')
def get_tree():
    return build_tree_html(BASE_DIR, is_root=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    folder = request.form.get('folder', '.')
    
    if not file or file.filename == '':
        return jsonify({"status": "error", "message": "Chưa chọn file!"})
    if file.filename.endswith('.py'):
        return jsonify({"status": "error", "message": "Bảo mật: Không được phép upload file code Python!"})

    target_dir = os.path.abspath(os.path.join(BASE_DIR, folder))
    if not target_dir.startswith(BASE_DIR):
        return jsonify({"status": "error", "message": "Lỗi bảo mật: Thư mục không hợp lệ!"})
        
    os.makedirs(target_dir, exist_ok=True)
    file.save(os.path.join(target_dir, file.filename))
    return jsonify({"status": "success", "message": f"Đã upload '{file.filename}' vào '{folder}'"})

@app.route('/delete', methods=['POST'])
def delete_file():
    rel_path = request.json.get('path', '')
    if rel_path.endswith('.py'):
        return jsonify({"status": "error", "message": "Bảo mật: Không được phép xóa file code!"})
        
    target_file = os.path.abspath(os.path.join(BASE_DIR, rel_path))
    if not target_file.startswith(BASE_DIR) or not os.path.isfile(target_file):
        return jsonify({"status": "error", "message": "Lỗi bảo mật: File không hợp lệ!"})
        
    try:
        os.remove(target_file)
        return jsonify({"status": "success", "message": f"Đã xóa file: {rel_path}"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Không thể xóa (File đang mở?): {str(e)}"})

@app.route('/build')
def build_manifest():
    try:
        result = subprocess.run(["python", "-X", "utf8", "ReleaseBuilder.py"], capture_output=True, text=True, check=True, encoding='utf-8')
        return jsonify({"status": "success", "message": "Build thành công!\n" + result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": f"Lỗi Build: {e.stderr}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/push')
def git_push():
    try:
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Auto Deploy Update"], check=True, capture_output=True)
        result = subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True, text=True, encoding='utf-8')
        return jsonify({"status": "success", "message": "Push lên GitHub thành công!\n" + result.stdout})
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in str(e.stdout):
            return jsonify({"status": "success", "message": "Code đã mới nhất, không có gì để push!"})
        return jsonify({"status": "error", "message": f"Lỗi Git: {e.stderr}"})

if __name__ == '__main__':
    print("🚀 Server Explorer đang chạy! Gửi IP:5000 cho sếp nhé!")
    app.run(host='0.0.0.0', port=5000, debug=True)