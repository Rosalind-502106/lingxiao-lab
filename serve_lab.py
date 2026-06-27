#!/usr/bin/env python
"""
凌逍科学社团 · 物资管理系统 - 服务器启动脚本
绑定所有网络接口 + 免费公网隧道 (localhost.run) + REST API
"""

import os
import sys
import io
import socket
import threading
import time
import json
import webbrowser
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 切换到项目目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

HOST = '0.0.0.0'
PORT = 8080
DATA_FILE = 'lab_data.json'

# ===================== 服务端数据存储 =====================

def load_server_data():
    """从服务器文件加载数据"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"  [!] Load server data failed: {e}")
    return None

def save_server_data(data):
    """保存数据到服务器文件"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"  [!] Save server data failed: {e}")
        return False

# ===================== 自定义 HTTP 处理器 =====================

class LabHTTPHandler(SimpleHTTPRequestHandler):
    """支持 API 和静态文件的 HTTP 处理器"""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API: 获取服务器数据
        if path == '/api/data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            data = load_server_data()
            if data is None:
                # 首次访问，返回空的默认结构
                data = {"items": [], "borrows": []}
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            return

        # 静态文件 - 使用父类处理
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API: 保存数据到服务器
        if path == '/api/data':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            try:
                data = json.loads(body.decode('utf-8'))
                ok = save_server_data(data)
                if ok:
                    result = {"status": "ok", "message": "数据已同步到服务器"}
                else:
                    result = {"status": "error", "message": "保存失败"}
            except Exception as e:
                result = {"status": "error", "message": str(e)}

            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Not Found')

    def do_OPTIONS(self):
        """CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """只显示 API 请求日志，过滤静态文件"""
        msg = format % args
        if '/api/' in msg:
            print(f"  [API] {msg}")

# ===================== 获取本机局域网IP =====================
def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

LAN_IP = get_lan_ip()

# ===================== HTTP 服务器 =====================
def start_http_server():
    server = HTTPServer((HOST, PORT), LabHTTPHandler)
    print(f"  [+] HTTP server running on 0.0.0.0:{PORT}")
    server.serve_forever()

# ===================== 获取公网网址 (localhost.run) =====================
def get_public_url():
    """使用 localhost.run 创建免费公网隧道（无需注册）"""
    print("  [*] Connecting to localhost.run (free tunnel, no signup required)...")
    try:
        ssh_cmd = [
            'ssh', '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=NUL',
            '-o', 'ServerAliveInterval=30',
            '-R', f'80:localhost:{PORT}',
            'nokey@localhost.run'
        ]
        proc = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        public_url = None
        start_time = time.time()
        while time.time() - start_time < 15:
            line = proc.stdout.readline()
            if line:
                line_stripped = line.strip()
                if line_stripped:
                    print(f"     {line_stripped}")
                # 提取公网 URL
                for keyword in ['https://', 'http://']:
                    if keyword in line and ('.lhr.life' in line or '.serveo.net' in line):
                        for word in line.split():
                            if word.startswith(keyword):
                                public_url = word.strip()
                                break
                if public_url:
                    break

        if public_url:
            full_url = f"{public_url.rstrip('/')}/index.html"
            api_url = f"{public_url.rstrip('/')}/api/data"
            print(f"\n  [✓] 公网地址 (手机/电脑共用):")
            print(f"      网页: {full_url}")
            print(f"      数据同步: {api_url}")
            print()
            return public_url

        print("  [X] localhost.run connection timed out. Serving LAN only.")
    except Exception as e:
        print(f"  [X] Tunnel error: {e}")

    return None

# ===================== 主程序 =====================
def main():
    banner = """
╔═══════════════════════════════════════════╗
║   凌逍科学社团 · 实验室物资管理系统 v2.1   ║
║        支持多设备数据云端同步 ✨           ║
╚═══════════════════════════════════════════╝
"""
    print(banner)

    # 启动 HTTP 服务器
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    time.sleep(0.5)

    print("  ── 访问地址 ──")
    print(f"  封面:   http://localhost:{PORT}/ (index.html)")
    print(f"  物资管理: http://localhost:{PORT}/lingxiao-lab-manager.html")
    print(f"  局域网: http://{LAN_IP}:{PORT}/")
    print(f"  API:    http://{LAN_IP}:{PORT}/api/data")
    print()
    print("  ── 正在获取公网地址（手机可访问）──")
    print()

    # 获取公网网址（后台线程）
    tunnel_thread = threading.Thread(target=get_public_url, daemon=True)
    tunnel_thread.start()

    # 自动打开浏览器
    time.sleep(1.5)
    try:
        webbrowser.open(f'http://localhost:{PORT}/')
    except:
        pass

    print()
    print("  按 Ctrl+C 停止服务器")
    print("  ─────────────────────────────────────")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  服务器已停止.")
        sys.exit(0)

if __name__ == '__main__':
    main()