"""
夸克网盘资源分享网站 - Flask 后端应用
"""
import json
import os
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# 初始化 Flask 应用
app = Flask(__name__)

# 加载配置
def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "site_title": "夸克资源站",
        "site_description": "精选优质资源分享",
        "admin_password": "admin123",
        "items_per_page": 12,
        "secret_key": "default-secret-key"
    }

def save_config(config):
    """保存配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# 加载配置
config = load_config()
app.secret_key = config.get('secret_key', 'default-secret-key')

# 数据文件路径
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'resources.json')
LOG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'login_log.json')
ANNOUNCEMENT_FILE = os.path.join(os.path.dirname(__file__), 'data', 'announcement.json')

def load_data():
    """加载资源数据"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"categories": [], "resources": []}

def save_data(data):
    """保存资源数据"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_login_log():
    """加载登录日志"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_login_log(logs):
    """保存登录日志"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    # 只保留最近100条记录
    logs = logs[-100:]
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def log_login_attempt(ip, success, user_agent=''):
    """记录登录尝试"""
    logs = load_login_log()
    logs.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": ip,
        "success": success,
        "user_agent": user_agent[:200] if user_agent else ''  # 限制长度
    })
    save_login_log(logs)

def load_announcement():
    """加载公告内容"""
    if os.path.exists(ANNOUNCEMENT_FILE):
        with open(ANNOUNCEMENT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 确保包含弹窗相关字段
            if 'popup_enabled' not in data:
                data['popup_enabled'] = False
            if 'popup_title' not in data:
                data['popup_title'] = data.get('title', '公告')
            if 'popup_content' not in data:
                data['popup_content'] = data.get('content', '')
            return data
    return {
        "enabled": True,
        "popup_enabled": False,
        "title": "欢迎访问",
        "content": "这是一个夸克网盘资源分享站，您可以在这里找到各种优质资源。",
        "popup_title": "欢迎访问",
        "popup_content": "这是一个夸克网盘资源分享站，您可以在这里找到各种优质资源。",
        "updated_at": datetime.now().isoformat()
    }

def save_announcement(announcement):
    """保存公告内容"""
    os.makedirs(os.path.dirname(ANNOUNCEMENT_FILE), exist_ok=True)
    announcement['updated_at'] = datetime.now().isoformat()
    with open(ANNOUNCEMENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(announcement, f, ensure_ascii=False, indent=2)

def login_required(f):
    """管理员登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.is_json:
                return jsonify({"error": "未授权访问"}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== 前台路由 ====================

@app.route('/')
def index():
    """前台首页"""
    config = load_config()
    data = load_data()
    return render_template('index.html', 
                         config=config, 
                         categories=data.get('categories', []))

@app.route('/api/resources')
def api_get_resources():
    """获取资源列表 API"""
    data = load_data()
    config = load_config()
    resources = data.get('resources', [])
    categories = data.get('categories', [])
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', config.get('items_per_page', 12), type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')
    
    # 筛选分类
    if category:
        resources = [r for r in resources if r.get('category') == category]
    
    # 搜索
    if search:
        search_lower = search.lower()
        resources = [r for r in resources if 
                    search_lower in r.get('title', '').lower() or 
                    search_lower in r.get('description', '').lower()]
    
    # 排序
    if sort == 'newest':
        resources.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    elif sort == 'oldest':
        resources.sort(key=lambda x: x.get('created_at', ''))
    elif sort == 'popular':
        resources.sort(key=lambda x: x.get('clicks', 0), reverse=True)
    elif sort == 'name':
        resources.sort(key=lambda x: x.get('title', ''))
    
    # 计算分页
    total = len(resources)
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    start = (page - 1) * limit
    end = start + limit
    
    # 获取分类信息映射
    category_map = {c['id']: c for c in categories}
    
    # 为每个资源添加分类信息
    paginated_resources = resources[start:end]
    for resource in paginated_resources:
        cat_id = resource.get('category', '')
        if cat_id in category_map:
            resource['category_info'] = category_map[cat_id]
    
    return jsonify({
        "resources": paginated_resources,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        }
    })

@app.route('/api/categories')
def api_get_categories():
    """获取分类列表 API"""
    data = load_data()
    categories = data.get('categories', [])
    
    # 计算每个分类的资源数量
    resources = data.get('resources', [])
    for category in categories:
        category['count'] = len([r for r in resources if r.get('category') == category['id']])
    
    return jsonify({"categories": categories})

@app.route('/api/announcement')
def api_get_announcement():
    """获取公告内容 API"""
    announcement = load_announcement()
    if not announcement.get('enabled', True):
        return jsonify({"enabled": False})
    return jsonify(announcement)

@app.route('/api/resources/<resource_id>/click', methods=['POST'])
def api_record_click(resource_id):
    """记录资源点击 API"""
    data = load_data()
    resources = data.get('resources', [])
    
    for resource in resources:
        if resource.get('id') == resource_id:
            resource['clicks'] = resource.get('clicks', 0) + 1
            save_data(data)
            return jsonify({"success": True, "clicks": resource['clicks']})
    
    return jsonify({"error": "资源不存在"}), 404

# ==================== 管理后台路由 ====================

@app.route('/admin')
@login_required
def admin_dashboard():
    """管理后台首页"""
    config = load_config()
    data = load_data()
    
    # 统计数据
    resources = data.get('resources', [])
    categories = data.get('categories', [])
    total_clicks = sum(r.get('clicks', 0) for r in resources)
    
    # 热门资源
    popular_resources = sorted(resources, key=lambda x: x.get('clicks', 0), reverse=True)[:5]
    
    return render_template('admin/dashboard.html',
                         config=config,
                         total_resources=len(resources),
                         total_categories=len(categories),
                         total_clicks=total_clicks,
                         popular_resources=popular_resources)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录"""
    config = load_config()
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        if password == config.get('admin_password'):
            session['admin_logged_in'] = True
            log_login_attempt(ip, True, user_agent)
            return redirect(url_for('admin_dashboard'))
        
        log_login_attempt(ip, False, user_agent)
        return render_template('admin/login.html', config=config, error="密码错误")
    
    return render_template('admin/login.html', config=config)

@app.route('/admin/logs')
@login_required
def admin_logs():
    """登录日志页面"""
    config = load_config()
    logs = load_login_log()
    # 倒序显示，最新的在前面
    logs = list(reversed(logs))
    return render_template('admin/logs.html', config=config, logs=logs)

@app.route('/admin/logout')
def admin_logout():
    """管理员退出"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin/resources')
@login_required
def admin_resources():
    """资源管理页面"""
    config = load_config()
    data = load_data()
    return render_template('admin/resources.html',
                         config=config,
                         categories=data.get('categories', []))

@app.route('/admin/categories')
@login_required
def admin_categories():
    """分类管理页面"""
    config = load_config()
    data = load_data()
    return render_template('admin/categories.html',
                         config=config,
                         categories=data.get('categories', []))

@app.route('/admin/settings')
@login_required
def admin_settings():
    """系统设置页面"""
    config = load_config()
    return render_template('admin/settings.html', config=config)

@app.route('/admin/announcement')
@login_required
def admin_announcement():
    """公告管理页面"""
    config = load_config()
    announcement = load_announcement()
    return render_template('admin/announcement.html', config=config, announcement=announcement)

# ==================== 管理 API ====================

@app.route('/api/admin/resources', methods=['GET'])
@login_required
def api_admin_get_resources():
    """获取资源列表（管理用）"""
    data = load_data()
    resources = data.get('resources', [])
    categories = data.get('categories', [])
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    search = request.args.get('search', '')
    
    # 搜索
    if search:
        search_lower = search.lower()
        resources = [r for r in resources if 
                    search_lower in r.get('title', '').lower() or 
                    search_lower in r.get('description', '').lower()]
    
    # 按创建时间倒序
    resources.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # 分页
    total = len(resources)
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    start = (page - 1) * limit
    end = start + limit
    
    # 获取分类信息
    category_map = {c['id']: c for c in categories}
    paginated_resources = resources[start:end]
    for resource in paginated_resources:
        cat_id = resource.get('category', '')
        if cat_id in category_map:
            resource['category_info'] = category_map[cat_id]
    
    return jsonify({
        "resources": paginated_resources,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    })

@app.route('/api/admin/resources', methods=['POST'])
@login_required
def api_admin_add_resource():
    """添加资源"""
    data = load_data()
    
    # 获取请求数据
    req_data = request.get_json()
    if not req_data:
        return jsonify({"error": "无效的请求数据"}), 400
    
    # 验证必填字段
    title = req_data.get('title', '').strip()
    link = req_data.get('link', '').strip()
    
    if not title:
        return jsonify({"error": "标题不能为空"}), 400
    if not link:
        return jsonify({"error": "链接不能为空"}), 400
    
    # 创建新资源
    now = datetime.now().isoformat()
    new_resource = {
        "id": f"res_{uuid.uuid4().hex[:8]}",
        "title": title,
        "description": req_data.get('description', '').strip(),
        "category": req_data.get('category', 'other'),
        "link": link,
        "size": req_data.get('size', '').strip(),
        "tags": req_data.get('tags', []),
        "clicks": 0,
        "created_at": now,
        "updated_at": now
    }
    
    data['resources'].append(new_resource)
    save_data(data)
    
    return jsonify({"success": True, "resource": new_resource})

@app.route('/api/admin/resources/<resource_id>', methods=['PUT'])
@login_required
def api_admin_update_resource(resource_id):
    """更新资源"""
    data = load_data()
    
    # 查找资源
    resource = None
    for r in data['resources']:
        if r.get('id') == resource_id:
            resource = r
            break
    
    if not resource:
        return jsonify({"error": "资源不存在"}), 404
    
    # 获取请求数据
    req_data = request.get_json()
    if not req_data:
        return jsonify({"error": "无效的请求数据"}), 400
    
    # 更新字段
    if 'title' in req_data:
        resource['title'] = req_data['title'].strip()
    if 'description' in req_data:
        resource['description'] = req_data['description'].strip()
    if 'category' in req_data:
        resource['category'] = req_data['category']
    if 'link' in req_data:
        resource['link'] = req_data['link'].strip()
    if 'size' in req_data:
        resource['size'] = req_data['size'].strip()
    if 'tags' in req_data:
        resource['tags'] = req_data['tags']
    
    resource['updated_at'] = datetime.now().isoformat()
    
    save_data(data)
    
    return jsonify({"success": True, "resource": resource})

@app.route('/api/admin/resources/<resource_id>', methods=['DELETE'])
@login_required
def api_admin_delete_resource(resource_id):
    """删除资源"""
    data = load_data()
    
    # 查找并删除资源
    original_len = len(data['resources'])
    data['resources'] = [r for r in data['resources'] if r.get('id') != resource_id]
    
    if len(data['resources']) == original_len:
        return jsonify({"error": "资源不存在"}), 404
    
    save_data(data)
    
    return jsonify({"success": True})

@app.route('/api/admin/resources/batch-delete', methods=['POST'])
@login_required
def api_admin_batch_delete_resources():
    """批量删除资源"""
    data = load_data()
    
    req_data = request.get_json()
    if not req_data or 'ids' not in req_data:
        return jsonify({"error": "无效的请求数据"}), 400
    
    ids_to_delete = set(req_data['ids'])
    original_len = len(data['resources'])
    data['resources'] = [r for r in data['resources'] if r.get('id') not in ids_to_delete]
    deleted_count = original_len - len(data['resources'])
    
    save_data(data)
    
    return jsonify({"success": True, "deleted_count": deleted_count})

# ==================== 分类管理 API ====================

@app.route('/api/admin/categories', methods=['POST'])
@login_required
def api_admin_add_category():
    """添加分类"""
    data = load_data()
    
    req_data = request.get_json()
    if not req_data:
        return jsonify({"error": "无效的请求数据"}), 400
    
    name = req_data.get('name', '').strip()
    if not name:
        return jsonify({"error": "分类名称不能为空"}), 400
    
    # 生成唯一ID
    cat_id = req_data.get('id', '').strip()
    if not cat_id:
        cat_id = f"cat_{uuid.uuid4().hex[:6]}"
    
    # 检查ID是否已存在
    existing_ids = [c['id'] for c in data.get('categories', [])]
    if cat_id in existing_ids:
        return jsonify({"error": "分类ID已存在"}), 400
    
    new_category = {
        "id": cat_id,
        "name": name,
        "icon": req_data.get('icon', '📁')
    }
    
    if 'categories' not in data:
        data['categories'] = []
    data['categories'].append(new_category)
    
    save_data(data)
    
    return jsonify({"success": True, "category": new_category})

@app.route('/api/admin/categories/<category_id>', methods=['PUT'])
@login_required
def api_admin_update_category(category_id):
    """更新分类"""
    data = load_data()
    
    # 查找分类
    category = None
    for c in data.get('categories', []):
        if c.get('id') == category_id:
            category = c
            break
    
    if not category:
        return jsonify({"error": "分类不存在"}), 404
    
    req_data = request.get_json()
    if not req_data:
        return jsonify({"error": "无效的请求数据"}), 400
    
    if 'name' in req_data:
        category['name'] = req_data['name'].strip()
    if 'icon' in req_data:
        category['icon'] = req_data['icon']
    
    save_data(data)
    
    return jsonify({"success": True, "category": category})

@app.route('/api/admin/categories/<category_id>', methods=['DELETE'])
@login_required
def api_admin_delete_category(category_id):
    """删除分类"""
    data = load_data()
    
    # 检查是否有资源使用该分类
    resources_using = [r for r in data.get('resources', []) if r.get('category') == category_id]
    if resources_using:
        return jsonify({
            "error": f"该分类下有 {len(resources_using)} 个资源，请先删除或移动这些资源"
        }), 400
    
    # 删除分类
    original_len = len(data.get('categories', []))
    data['categories'] = [c for c in data.get('categories', []) if c.get('id') != category_id]
    
    if len(data['categories']) == original_len:
        return jsonify({"error": "分类不存在"}), 404
    
    save_data(data)
    
    return jsonify({"success": True})

# ==================== 系统设置 API ====================

@app.route('/api/admin/password', methods=['PUT'])
@login_required
def api_admin_change_password():
    """修改密码"""
    config = load_config()
    
    req_data = request.get_json()
    if not req_data:
        return jsonify({"error": "无效的请求数据"}), 400
    
    old_password = req_data.get('old_password', '')
    new_password = req_data.get('new_password', '')
    
    if old_password != config.get('admin_password'):
        return jsonify({"error": "原密码错误"}), 400
    
    if len(new_password) < 4:
        return jsonify({"error": "新密码长度至少4位"}), 400
    
    config['admin_password'] = new_password
    save_config(config)
    
    return jsonify({"success": True})

@app.route('/api/admin/settings', methods=['PUT'])
@login_required
def api_admin_update_settings():
    """更新网站设置"""
    config = load_config()
    
    req_data = request.get_json()
    if not req_data:
        return jsonify({"error": "无效的请求数据"}), 400
    
    if 'site_title' in req_data:
        config['site_title'] = req_data['site_title'].strip()
    if 'site_description' in req_data:
        config['site_description'] = req_data['site_description'].strip()
    if 'items_per_page' in req_data:
        config['items_per_page'] = int(req_data['items_per_page'])
    
    save_config(config)
    
    return jsonify({"success": True, "config": {
        "site_title": config.get('site_title'),
        "site_description": config.get('site_description'),
        "items_per_page": config.get('items_per_page')
    }})

# ==================== 公告管理 API ====================

@app.route('/api/admin/announcement', methods=['GET'])
@login_required
def api_admin_get_announcement():
    """获取公告内容（管理用）"""
    announcement = load_announcement()
    return jsonify(announcement)

@app.route('/api/admin/announcement', methods=['PUT'])
@login_required
def api_admin_update_announcement():
    """更新公告内容"""
    req_data = request.get_json()
    if not req_data:
        return jsonify({"error": "无效的请求数据"}), 400
    
    announcement = load_announcement()
    
    # 横幅公告设置
    if 'enabled' in req_data:
        announcement['enabled'] = bool(req_data['enabled'])
    if 'title' in req_data:
        announcement['title'] = req_data['title'].strip()
    if 'content' in req_data:
        announcement['content'] = req_data['content'].strip()
    
    # 弹窗公告设置
    if 'popup_enabled' in req_data:
        announcement['popup_enabled'] = bool(req_data['popup_enabled'])
    if 'popup_title' in req_data:
        announcement['popup_title'] = req_data['popup_title'].strip()
    if 'popup_content' in req_data:
        announcement['popup_content'] = req_data['popup_content'].strip()
    
    save_announcement(announcement)
    
    return jsonify({"success": True, "announcement": announcement})

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(e):
    """404 错误页面"""
    if request.path.startswith('/api/'):
        return jsonify({"error": "接口不存在"}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """500 错误页面"""
    if request.path.startswith('/api/'):
        return jsonify({"error": "服务器内部错误"}), 500
    return render_template('500.html'), 500

# ==================== 启动应用 ====================

if __name__ == '__main__':
    # 确保数据目录存在
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    # 如果数据文件不存在，创建初始数据
    if not os.path.exists(DATA_FILE):
        initial_data = {
            "categories": [
                {"id": "games", "name": "游戏", "icon": "🎮"},
                {"id": "software", "name": "软件", "icon": "💻"},
                {"id": "movies", "name": "影视", "icon": "🎬"},
                {"id": "music", "name": "音乐", "icon": "🎵"},
                {"id": "ebooks", "name": "电子书", "icon": "📚"},
                {"id": "other", "name": "其他", "icon": "📦"}
            ],
            "resources": []
        }
        save_data(initial_data)
    
    # 启动开发服务器
    app.run(host='0.0.0.0', port=5001, debug=True)