#!/usr/bin/env python
"""
凌逍科学社团 · 资产管理系统
Flask 后端服务器 - 支持多设备数据云端同步
部署到 Render 云平台
"""
import os
import sys
import io
import json
import time
import hashlib
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory

# Windows console encoding fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
DATA_FILE = DATA_DIR / 'lab_data.json'
BACKUP_DIR = DATA_DIR / 'backups'
LOG_FILE = DATA_DIR / 'operation_log.json'

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder='.', static_url_path='')

# 手动 CORS 支持（无需安装 flask-cors）
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

# 管理员密码（可从环境变量读取，更安全）
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'lingxiao2025')

# ---------------------------------------------------------------------------
# 数据操作锁（保证并发安全）
# ---------------------------------------------------------------------------
data_lock = threading.Lock()


# ---------------------------------------------------------------------------
# 数据加载与保存
# ---------------------------------------------------------------------------
def load_data():
    """从 JSON 文件加载数据"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[!] 数据文件损坏，尝试从备份恢复: {e}")
            # 尝试从最近的备份恢复
            restored = restore_from_backup()
            if restored:
                return restored
            return {"items": [], "borrows": [], "operations": []}
    return {"items": [], "borrows": [], "operations": []}


def save_data(data):
    """保存数据到 JSON 文件（线程安全）"""
    with data_lock:
        try:
            # 先写入临时文件，再原子替换，防止写入中断导致数据损坏
            tmp_file = DATA_FILE.with_suffix('.tmp')
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            tmp_file.replace(DATA_FILE)
            return True
        except Exception as e:
            print(f"[!] 保存数据失败: {e}")
            return False


def create_backup(data):
    """创建数据备份"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f'lab_data_{timestamp}.json'
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # 只保留最近 50 个备份
        cleanup_old_backups(50)
        return True
    except Exception as e:
        print(f"[!] 备份失败: {e}")
        return False


def cleanup_old_backups(max_count=50):
    """清理旧备份，只保留最新的 max_count 个"""
    backups = sorted(BACKUP_DIR.glob('lab_data_*.json'), reverse=True)
    for old_file in backups[max_count:]:
        try:
            old_file.unlink()
        except OSError:
            pass


def restore_from_backup():
    """从最近的备份恢复数据"""
    backups = sorted(BACKUP_DIR.glob('lab_data_*.json'), reverse=True)
    for backup_file in backups:
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[✓] 从备份恢复成功: {backup_file.name}")
            # 恢复到主文件
            save_data(data)
            return data
        except Exception as e:
            print(f"[!] 备份 {backup_file.name} 也损坏: {e}")
    return None


def compute_data_hash(data):
    """计算数据哈希，用于同步检测"""
    serialized = json.dumps(data, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(serialized.encode('utf-8')).hexdigest()


def log_operation(action, detail="", operator="unknown"):
    """记录操作日志"""
    data = load_data()
    if "operations" not in data:
        data["operations"] = []
    data["operations"].append({
        "time": datetime.now().isoformat(),
        "action": action,
        "detail": detail,
        "operator": operator
    })
    # 只保留最近 500 条操作记录
    if len(data["operations"]) > 500:
        data["operations"] = data["operations"][-500:]
    save_data(data)


# ---------------------------------------------------------------------------
# 定时备份
# ---------------------------------------------------------------------------
def auto_backup():
    """每 5 分钟自动备份一次"""
    while True:
        time.sleep(300)
        try:
            data = load_data()
            create_backup(data)
        except Exception as e:
            print(f"[!] 自动备份失败: {e}")


# ---------------------------------------------------------------------------
# API 路由
# ---------------------------------------------------------------------------
@app.route('/api/health')
def health_check():
    """健康检查接口"""
    data = load_data()
    items = data.get("items", [])
    borrows = data.get("borrows", [])
    active_borrows = [b for b in borrows if not b.get("returned")]
    return jsonify({
        "status": "ok",
        "version": "3.0",
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "items_count": len(items),
            "borrows_count": len(active_borrows)
        }
    })


@app.route('/api/data')
def get_data():
    """获取完整数据"""
    data = load_data()
    # 不返回操作日志给前端
    response_data = {
        "items": data.get("items", []),
        "borrows": data.get("borrows", [])
    }
    response = jsonify(response_data)
    # 添加数据哈希头，便于前端判断是否有变化
    response.headers['X-Data-Hash'] = compute_data_hash(response_data)
    return response


@app.route('/api/data/hash')
def get_data_hash():
    """获取当前数据哈希（轻量级检查）"""
    data = load_data()
    response_data = {
        "items": data.get("items", []),
        "borrows": data.get("borrows", [])
    }
    return jsonify({
        "hash": compute_data_hash(response_data),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/data', methods=['POST'])
def save_data_api():
    """保存数据（从前端推送）"""
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"status": "error", "message": "无效的 JSON 数据"}), 400

    # 验证数据结构
    if not isinstance(body.get("items"), list):
        return jsonify({"status": "error", "message": "数据格式错误：items 必须是数组"}), 400
    if not isinstance(body.get("borrows"), list):
        return jsonify({"status": "error", "message": "数据格式错误：borrows 必须是数组"}), 400

    success = save_data(body)
    if success:
        # 创建备份
        threading.Thread(target=create_backup, args=(body,), daemon=True).start()
        return jsonify({
            "status": "ok",
            "message": "数据已同步到服务器",
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({"status": "error", "message": "保存失败，请重试"}), 500


@app.route('/api/data/sync', methods=['POST'])
def sync_data():
    """
    智能同步接口：客户端发送本地数据，服务端对比并返回最新数据
    采用"最后写入者胜出"策略
    """
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"status": "error", "message": "无效的 JSON 数据"}), 400

    server_data = load_data()
    client_data = body.get("data", {})
    client_timestamp = body.get("timestamp", "")

    server_response = {
        "items": server_data.get("items", []),
        "borrows": server_data.get("borrows", [])
    }
    server_hash = compute_data_hash(server_response)

    # 如果客户端没有提供数据或时间戳，直接返回服务器数据
    if not client_data or not client_timestamp:
        return jsonify({
            "status": "synced",
            "data": server_response,
            "hash": server_hash,
            "timestamp": datetime.now().isoformat()
        })

    client_hash = body.get("hash", "")
    # 如果哈希相同，无需同步
    if client_hash == server_hash:
        return jsonify({
            "status": "up_to_date",
            "hash": server_hash,
            "timestamp": datetime.now().isoformat()
        })

    # 哈希不同，返回服务器最新数据
    return jsonify({
        "status": "synced",
        "data": server_response,
        "hash": server_hash,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/stats')
def get_stats():
    """获取统计数据"""
    data = load_data()
    items = data.get("items", [])
    borrows = data.get("borrows", [])
    active_borrows = [b for b in borrows if not b.get("returned")]

    available = 0
    for item in items:
        borrowed_qty = sum(
            b.get("qty", 0) for b in active_borrows if b.get("itemId") == item.get("id")
        )
        available += max(0, (int(item.get("total", 0)) - borrowed_qty))

    return jsonify({
        "total_items": len(items),
        "active_borrows": len(active_borrows),
        "available_items": available,
        "total_categories": len(set(i.get("category", "其他") for i in items))
    })


@app.route('/api/operations')
def get_operations():
    """获取最近的操作日志"""
    data = load_data()
    ops = data.get("operations", [])[-100:]  # 最近 100 条
    return jsonify({"operations": ops})


@app.route('/api/admin/verify', methods=['POST'])
def verify_admin():
    """验证管理员密码"""
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "无效请求"}), 400

    password = body.get("password", "")
    if password == ADMIN_PASSWORD:
        return jsonify({"status": "ok", "message": "验证成功"})
    else:
        return jsonify({"status": "error", "message": "密码错误"}), 401


@app.route('/api/export')
def export_data():
    """导出完整数据（包含备份和操作日志）"""
    data = load_data()
    export = {
        "version": "3.0",
        "exported_at": datetime.now().isoformat(),
        "data": data,
        "stats": {
            "items": len(data.get("items", [])),
            "borrows": len(data.get("borrows", [])),
            "operations": len(data.get("operations", []))
        }
    }
    return jsonify(export)


# ---------------------------------------------------------------------------
# 静态文件服务
# ---------------------------------------------------------------------------
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'lingxiao-lab-manager.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


# ---------------------------------------------------------------------------
# 错误处理
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "接口不存在"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"status": "error", "message": "服务器内部错误"}), 500


# ---------------------------------------------------------------------------
# 启动
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 56)
    print("  凌逍科学社团 · 资产管理系统 v3.0")
    print("  后端服务器 (Flask)")
    print("=" * 56)
    print()

    # 启动自动备份线程
    backup_thread = threading.Thread(target=auto_backup, daemon=True)
    backup_thread.start()

    # 从环境变量读取端口（Render 会自动设置 PORT）
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'

    print(f"  [✓] 数据目录: {DATA_DIR}")
    print(f"  [✓] 备份目录: {BACKUP_DIR}")
    print(f"  [✓] 服务器启动: http://0.0.0.0:{port}")
    print()

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True  # 多线程处理请求
    )