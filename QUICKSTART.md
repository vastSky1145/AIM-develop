# 快速开始指南

## 🚀 5分钟快速部署

### 前置要求

1. **Python 3.8+**
2. **MongoDB** (运行在本地或远程)
3. **PowerPoint** (仅Windows，用于PPT解析)

### 步骤一：安装依赖

```bash
pip install -r requirements_fastapi.txt
```

### 步骤二：配置环境

复制配置文件并修改：

```bash
# Linux/Mac
cp .env.example .env

# Windows
copy .env.example .env
```

编辑`.env`文件，至少需要配置：
- `JWT_SECRET_KEY`: 改为一个随机字符串
- `GEMINI_API_KEY`: 你的Gemini API密钥（如果使用）

### 步骤三：启动MongoDB

```bash
# Windows
net start MongoDB

# Linux
sudo systemctl start mongod

# Mac
brew services start mongodb-community
```

### 步骤四：启动服务器

```bash
# 方式1: 使用启动脚本（推荐）
# Windows
start_server.bat

# Linux/Mac
chmod +x start_server.sh
./start_server.sh

# 方式2: 直接运行
python app.py
```

### 步骤五：访问API文档

打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **前端示例**: 打开 `example_frontend.html`

## 📝 第一次使用

### 1. 创建用户

目前需要手动在MongoDB中创建用户。打开MongoDB客户端：

```javascript
// 使用research_papers数据库
use research_papers

// 创建用户（密码需要bcrypt加密）
db.users.insertOne({
    username: "sxs",
    password_hash: "$2b$12$...",  // 使用bcrypt加密后的密码
    email: "user@example.com"
})
```

或者使用Python生成加密密码：

```python
import bcrypt

password = "123456"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed)
```

### 2. 测试登录

```bash
# 运行测试脚本
python test_api.py
```

或使用curl：

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "sxs", "password": "123456"}'
```

### 3. 使用前端示例

1. 打开 `example_frontend.html`
2. 输入用户名和密码
3. 点击"登录"
4. 测试其他功能

## 🔧 常见问题

### Q: MongoDB连接失败？

```bash
# 检查MongoDB是否运行
# Windows
sc query MongoDB

# Linux
systemctl status mongod

# 如果未运行，启动它
net start MongoDB  # Windows
sudo systemctl start mongod  # Linux
```

### Q: 找不到某个Python包？

```bash
# 重新安装所有依赖
pip install -r requirements_fastapi.txt --force-reinstall
```

### Q: PPT上传失败？

确保：
1. Windows系统
2. 已安装PowerPoint
3. PPT文件格式正确（.ppt或.pptx）

### Q: 向量数据库初始化慢？

首次运行时会下载HuggingFace模型，可能需要几分钟。耐心等待。

### Q: Token过期？

Token默认7天有效期，过期后重新登录即可。

## 📚 下一步

- 阅读 [API文档](README_API.md)
- 查看 [Swagger UI](http://localhost:8000/docs)
- 尝试上传PPT和PDF
- 使用AI生成功能

## 🆘 获取帮助

如遇问题：
1. 查看控制台日志
2. 检查MongoDB连接
3. 确认环境变量配置
4. 提交Issue

## 🎉 开始使用

现在你可以：
- ✅ 上传PPT解析为论文结构
- ✅ 管理多篇论文
- ✅ 上传PDF到知识库
- ✅ 使用AI辅助写作
- ✅ 检索知识库内容
- ✅ 自定义Prompt模板

祝使用愉快！🚀

