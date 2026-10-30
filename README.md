# E_Shop_System 部署指南

本文档说明如何从 GitHub 下载本项目并完成本地运行或 Linux 服务器部署。

## 1. 项目说明

项目由两个部分构成：

- 后端：Django + Django REST Framework + MySQL
- 前端：React 18

GitHub 仓库只包含源代码和依赖清单，不包含以下本机文件：

- Python 虚拟环境目录
- node_modules
- Python 缓存文件
- React 构建目录
- 数据库导出文件
- 用户上传的媒体文件
- 包含真实密码的 .env 配置

因此下载后必须安装依赖、配置数据库并初始化表结构。

## 2. 环境要求

请先安装：

- Python 3.10 或更高版本
- Node.js 18 或更高版本
- npm
- MySQL 8
- Git

检查版本：

python --version
node --version
npm --version
mysql --version

Windows 用户也可以使用 PowerShell 完成以下本地部署步骤。

## 3. 下载项目

git clone https://github.com/你的用户名/E_Shop_System.git
cd E_Shop_System

## 4. 创建数据库

使用 MySQL 管理员账户登录：

mysql -u root -p

执行下面的 SQL。请将示例密码替换成自己的强密码：

CREATE DATABASE eshop_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'eshop_user'@'localhost'
  IDENTIFIED BY '请替换为你的数据库密码';

GRANT ALL PRIVILEGES ON eshop_db.*
  TO 'eshop_user'@'localhost';

FLUSH PRIVILEGES;

如果本机已经存在 eshop_db，不要重复创建，但需要确认账号具有读写权限。

## 5. 安装后端依赖

### Windows PowerShell

在项目根目录执行：

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install "django-extensions>=3.2"

如果 PowerShell 禁止运行激活脚本，可以先执行：

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

### Linux

在项目根目录执行：

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install "django-extensions>=3.2"

如果安装 mysqlclient 时提示缺少 MySQL 开发库，可参考所用 Linux 发行版安装 MySQL 客户端开发包、Python 开发包、编译器和 pkg-config。

当前 requirements.txt 尚未包含 django-extensions，所以必须额外执行一次上面的安装命令。如果以后把它加入依赖清单，就不需要单独安装。

正确读取依赖清单的命令是：

pip install -r requirements.txt

## 6. 配置后端环境变量

当前 Django 设置通过系统环境变量读取配置，不会自动加载 .env 文件。请在当前终端中设置变量。

### Windows PowerShell

$env:DJANGO_DEBUG="True"
$env:DJANGO_SECRET_KEY="请替换为足够长的随机字符串"
$env:DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1"
$env:DB_NAME="eshop_db"
$env:DB_USER="eshop_user"
$env:DB_PASSWORD="请替换为你的数据库密码"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"

### Linux

export DJANGO_DEBUG="True"
export DJANGO_SECRET_KEY="请替换为足够长的随机字符串"
export DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1"
export DB_NAME="eshop_db"
export DB_USER="eshop_user"
export DB_PASSWORD="请替换为你的数据库密码"
export DB_HOST="127.0.0.1"
export DB_PORT="3306"

这些环境变量只在当前终端会话中有效。关闭终端后需要重新设置。

## 7. 初始化并启动后端

在项目根目录执行：

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000

后端启动后：

- API 地址：http://127.0.0.1:8000/api/
- Django 管理后台：http://127.0.0.1:8000/admin/

runserver 适合本地开发，不建议直接用于公开服务器。

## 8. 安装并启动前端

另开一个终端，进入前端目录：

cd frontend
npm ci

创建 frontend/.env 并填写后端地址：

PORT=3030
REACT_APP_API_URL=http://127.0.0.1:8000

注意：REACT_APP_API_URL 只填写后端主机和端口，不要在后面添加 /api。前端请求路径本身已经包含 /api。

Windows 启动：

cd frontend
npm start

Linux 或 macOS 启动：

cd frontend
PORT=3030 npx react-scripts start

浏览器访问：

http://localhost:3030

## 9. 初始化商品数据

数据库导出文件和媒体文件没有上传到 GitHub，因此新环境初始化后是空数据库。

完成迁移后，可执行：

python manage.py createsuperuser

然后访问：

http://127.0.0.1:8000/admin/

通过管理后台添加商品、分类等测试数据。

如果项目提供脱敏后的 Django fixture，也可以使用：

python manage.py loaddata 数据文件名.json

不要直接使用包含真实用户、订单或密码字段的数据库导出文件。

## 10. Linux 服务器部署

以下示例假设：

- 项目目录：/opt/e_shop
- 域名：shop.example.com
- 后端监听：127.0.0.1:8000
- Nginx 对外监听：80

### 10.1 安装运行依赖

安装 Nginx、MySQL、Python 虚拟环境支持和 mysqlclient 编译依赖。具体包名根据 Ubuntu、Debian 或 CentOS 调整。

在服务器上安装 Python 依赖和 Gunicorn：

cd /opt/e_shop
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install "django-extensions>=3.2" gunicorn

### 10.2 设置生产环境变量

创建仅服务器管理员可读的环境变量文件：

sudo nano /etc/e-shop.env

写入以下内容，并替换成真实值：

DJANGO_DEBUG=False
DJANGO_SECRET_KEY=替换为随机生成的长密钥
DJANGO_ALLOWED_HOSTS=shop.example.com
DB_NAME=eshop_db
DB_USER=eshop_user
DB_PASSWORD=替换为数据库强密码
DB_HOST=127.0.0.1
DB_PORT=3306

限制文件权限：

sudo chmod 600 /etc/e-shop.env

### 10.3 构建前端

cd /opt/e_shop/frontend
npm ci
REACT_APP_API_URL="" npm run build

生产环境使用空地址，让浏览器通过同域名下的 /api/ 请求后端。

### 10.4 收集 Django 静态文件

cd /opt/e_shop
set -a
source /etc/e-shop.env
set +a
source .venv/bin/activate
python manage.py collectstatic --noinput
python manage.py migrate

### 10.5 使用 systemd 启动 Gunicorn

创建服务文件：

sudo nano /etc/systemd/system/e-shop.service

示例内容：

[Unit]
Description=E_Shop Django service
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/e_shop
EnvironmentFile=/etc/e-shop.env
ExecStart=/opt/e_shop/.venv/bin/gunicorn \
  backend.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 3
Restart=always

[Install]
WantedBy=multi-user.target

确保运行用户能够读取项目文件和媒体目录：

sudo chown -R www-data:www-data /opt/e_shop/media /opt/e_shop/staticfiles
sudo systemctl daemon-reload
sudo systemctl enable --now e-shop
sudo systemctl status e-shop

### 10.6 配置 Nginx

创建站点配置：

sudo nano /etc/nginx/sites-available/e-shop

示例内容：

server {
    listen 80;
    server_name shop.example.com;

    root /opt/e_shop/frontend/build;
    index index.html;

    client_max_body_size 20m;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Admin 静态资源
    location /static/admin/ {
        alias /opt/e_shop/staticfiles/admin/;
    }

    # React 构建后的静态资源
    location /static/ {
        try_files $uri =404;
    }

    location /media/ {
        alias /opt/e_shop/media/;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}

启用站点并检查配置：

sudo ln -s /etc/nginx/sites-available/e-shop /etc/nginx/sites-enabled/e-shop
sudo nginx -t
sudo systemctl reload nginx

最后将域名解析到服务器公网 IP，并确认防火墙已开放 80 和 443 端口。正式上线建议配置 HTTPS。

## 11. 常见问题

### 后端提示 No module named 'django_extensions'

执行：

python -m pip install "django-extensions>=3.2"

### 后端无法连接 MySQL

检查：

- MySQL 服务是否启动
- DB_NAME、DB_USER、DB_PASSWORD 是否正确
- 数据库账号是否有权限
- DB_HOST 和 DB_PORT 是否正确

### 前端页面能打开，但接口请求失败

检查 frontend/.env：

REACT_APP_API_URL=http://127.0.0.1:8000

修改环境变量后必须重启前端开发服务器。

### 生产环境刷新页面后出现 404

确认 Nginx 包含：

location / {
    try_files $uri $uri/ /index.html;
}

### 商品图片上传后无法显示

检查 MEDIA_ROOT 对应目录及 Nginx 的 /media/ 配置，并确保 Gunicorn 和 Nginx 运行用户具有目录读取权限。

