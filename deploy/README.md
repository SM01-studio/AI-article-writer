# AI Article Writer 部署指南

本目录包含服务器部署所需的配置文件。

## 文件说明

| 文件 | 说明 |
|------|------|
| `api-server.service` | Systemd 服务配置文件 |
| `nginx.conf` | Nginx 反向代理配置 |

## 部署步骤

### 1. 服务器环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 3.10+
sudo apt install python3.10 python3-pip python3-venv -y

# 安装 Nginx
sudo apt install nginx -y

# 安装 Git
sudo apt install git -y
```

### 2. 克隆代码

```bash
# 克隆仓库
cd /home/ubuntu
git clone https://github.com/your-username/ai-article-writer.git
cd ai-article-writer
```

### 3. 配置 Python 环境

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
cd ai-article-writer
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量，填入 API Keys
nano .env
```

需要配置的环境变量：
- `GLM_API_KEY` - 智谱 AI API Key
- `GEMINI_API_KEY` - Gemini API Key
- `SECRET_KEY` - Flask 密钥（随机字符串）
- `ALLOWED_ORIGINS` - 允许的跨域来源

### 5. 配置 Systemd 服务

```bash
# 复制服务配置文件
sudo cp deploy/api-server.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start api-server

# 设置开机自启
sudo systemctl enable api-server

# 查看服务状态
sudo systemctl status api-server
```

### 6. 配置 Nginx

```bash
# 复制 Nginx 配置
sudo cp deploy/nginx.conf /etc/nginx/sites-available/api-server

# 修改配置中的域名
sudo nano /etc/nginx/sites-available/api-server
# 将 api.your-domain.com 替换为你的实际域名

# 创建软链接
sudo ln -s /etc/nginx/sites-available/api-server /etc/nginx/sites-enabled/

# 删除默认配置（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

### 7. 配置 SSL 证书（推荐）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d api.your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

### 8. 防火墙配置

```bash
# 允许 HTTP 和 HTTPS
sudo ufw allow 'Nginx Full'

# 启用防火墙
sudo ufw enable
```

## 常用命令

```bash
# 查看服务状态
sudo systemctl status api-server

# 重启服务
sudo systemctl restart api-server

# 查看日志
sudo journalctl -u api-server -f

# 重载 Nginx
sudo systemctl reload nginx

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

## 故障排查

### 服务无法启动

1. 检查环境变量是否正确配置
2. 检查 Python 依赖是否安装完整
3. 查看服务日志：`sudo journalctl -u api-server -n 50`

### API 无法访问

1. 检查 Nginx 配置是否正确
2. 检查防火墙是否开放端口
3. 检查服务是否正在运行

### CORS 错误

1. 检查 `.env` 中的 `ALLOWED_ORIGINS` 配置
2. 确保前端域名已添加到允许列表

## 更新部署

```bash
cd /home/ubuntu/ai-article-writer
git pull
source .venv/bin/activate
cd ai-article-writer
pip install -r requirements.txt
sudo systemctl restart api-server
```
