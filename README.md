# 🌟 夸克网盘资源分享网站

一个简单轻量的夸克网盘资源链接分享网站，支持资源分类、搜索、排序，以及后台管理功能。

## ✨ 功能特性

### 前台功能
- 📦 资源卡片展示（磨砂玻璃暗黑主题）
- 🏷️ 自定义分类筛选
- 🔍 关键词搜索
- 📊 多种排序方式（最新/最热门/最早/名称）
- 👆 点击量统计
- 📱 响应式设计（支持手机/平板/电脑）

### 管理后台
- 🔐 密码保护登录
- 📦 资源增删改查
- 🏷️ 自定义分类管理
- 🗑️ 批量删除
- 🔑 修改管理密码
- ⚙️ 网站设置

## 🛠️ 技术栈

- **后端**: Python Flask
- **前端**: HTML + TailwindCSS + Alpine.js
- **数据存储**: JSON 文件
- **UI 风格**: 磨砂玻璃 + 暗黑主题

## 📁 项目结构

```
quark-share/
├── app.py              # Flask 主应用
├── config.json         # 网站配置
├── requirements.txt    # Python 依赖
├── README.md           # 使用说明
├── data/
│   └── resources.json  # 资源数据
├── templates/          # HTML 模板
│   ├── base.html
│   ├── index.html
│   ├── 404.html
│   ├── 500.html
│   └── admin/
│       ├── base.html
│       ├── login.html
│       ├── dashboard.html
│       ├── resources.html
│       ├── categories.html
│       └── settings.html
└── static/
    └── css/
        └── custom.css  # 自定义样式
```

## 🚀 快速开始

### Windows 本地测试

1. **确保已安装 Python 3.8+**
   ```bash
   python --version
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **运行应用**
   ```bash
   python app.py
   ```

5. **访问网站**
   - 前台: http://localhost:5000
   - 后台: http://localhost:5000/admin
   - 默认密码: `admin123`

### Ubuntu 服务器部署

1. **安装 Python**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```

2. **上传项目文件**
   ```bash
   # 使用 SCP 或 SFTP 上传项目到服务器
   # 例如上传到 /var/www/quark-share
   ```

3. **创建虚拟环境并安装依赖**
   ```bash
   cd /var/www/quark-share
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

4. **测试运行**
   ```bash
   python app.py
   ```

5. **使用 Gunicorn 生产运行**
   ```bash
   gunicorn -w 2 -b 0.0.0.0:5000 app:app
   ```

6. **配置 Systemd 服务（可选，推荐）**

   创建服务文件 `/etc/systemd/system/quark-share.service`:
   ```ini
   [Unit]
   Description=Quark Share Web App
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/quark-share
   Environment="PATH=/var/www/quark-share/venv/bin"
   ExecStart=/var/www/quark-share/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   启用并启动服务:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable quark-share
   sudo systemctl start quark-share
   sudo systemctl status quark-share
   ```

7. **配置 Nginx 反向代理（可选，推荐）**

   创建 Nginx 配置 `/etc/nginx/sites-available/quark-share`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;  # 替换为你的域名

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /static {
           alias /var/www/quark-share/static;
           expires 30d;
       }
   }
   ```

   启用配置:
   ```bash
   sudo ln -s /etc/nginx/sites-available/quark-share /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## ⚙️ 配置说明

### config.json

```json
{
  "site_title": "夸克资源站",      // 网站标题
  "site_description": "精选优质资源分享",  // 网站描述
  "admin_password": "admin123",   // 管理密码（请修改！）
  "items_per_page": 12,           // 每页显示数量
  "secret_key": "your-secret-key" // Session 密钥（请修改！）
}
```

### data/resources.json

资源数据文件，包含分类和资源列表。

## 🔒 安全建议

1. **修改默认密码**: 首次使用请立即修改 `admin123` 为强密码
2. **修改 Secret Key**: 生产环境请修改 `config.json` 中的 `secret_key`
3. **使用 HTTPS**: 生产环境建议配置 SSL 证书
4. **定期备份**: 定期备份 `data/resources.json` 和 `config.json`

## 📝 使用说明

### 添加资源

1. 访问管理后台 `/admin`
2. 输入管理密码登录
3. 点击「资源管理」→「添加资源」
4. 填写资源信息：
   - 标题（必填）
   - 夸克网盘链接（必填）
   - 描述
   - 分类
   - 文件大小

### 管理分类

1. 在管理后台点击「分类管理」
2. 可以添加、编辑、删除分类
3. 每个分类可设置名称和 Emoji 图标

### 修改密码

1. 在管理后台点击「系统设置」
2. 输入当前密码和新密码
3. 点击「修改密码」

## 🐛 常见问题

**Q: 如何重置管理密码？**
A: 直接编辑 `config.json` 文件，修改 `admin_password` 字段。

**Q: 资源数据存在哪里？**
A: 存储在 `data/resources.json` 文件中。

**Q: 如何备份数据？**
A: 备份 `data/` 目录和 `config.json` 文件即可。

**Q: 支持多少资源？**
A: 使用 JSON 文件存储，建议控制在数千条以内。如需更大规模，建议使用数据库。

## 📄 许可证

MIT License

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/)
- [TailwindCSS](https://tailwindcss.com/)
- [Alpine.js](https://alpinejs.dev/)