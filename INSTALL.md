# 安装与配置指南 (INSTALL.md)

本文档指导如何在本地或服务器中为 AI 编程助手部署并配置 `skill-ima-knowledge-base`。

---

## 1. 运行前提

- **操作系统**：Windows 10/11、macOS 或 Linux。
- **Python 版本**：Python 3.8 或更高版本（推荐 3.10+）。
- **Python 依赖**：安装 `requests`。

```bash
python -m pip install --upgrade requests
```

---

## 2. 凭证配置

腾讯 ima OpenAPI 采用 `Client ID` + `API Key` 双凭证认证。

### 步骤 1：获取凭证
1. 访问腾讯 ima 开放平台接口管理页：[https://ima.qq.com/agent-interface](https://ima.qq.com/agent-interface)。
2. 使用微信或 QQ 扫码登录。
3. 点击「创建凭证」（或「生成新凭证」）。
4. 复制生成的 **Client ID** 和 **API Key**（注意：API Key 仅完整显示一次，请妥善保存）。

### 步骤 2：持久化凭证（推荐方式）

#### 方式 A：操作系统用户目录（跨项目全局生效，最推荐）
在当前用户主目录下创建配置目录并写入文件：

**Windows (PowerShell)**:
```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.config\ima"
"你的_Client_ID" | Out-File -Encoding utf8 -NoNewline "$HOME\.config\ima\client_id"
"你的_API_Key"   | Out-File -Encoding utf8 -NoNewline "$HOME\.config\ima\api_key"
```

**macOS / Linux (Bash)**:
```bash
mkdir -p ~/.config/ima
echo -n "你的_Client_ID" > ~/.config/ima/client_id
echo -n "你的_API_Key" > ~/.config/ima/api_key
chmod 600 ~/.config/ima/*
```

#### 方式 B：本地 `.env` 隔离文件（仅当前技能项目生效）
在技能根目录下复制 `.env.example`：
```bash
cp .env.example .env
```
编辑 `.env`：
```env
IMA_CLIENT_ID="你的_Client_ID"
IMA_API_KEY="你的_API_Key"
```

---

## 3. 健康检查与验收

在终端执行探活命令：

```bash
python scripts/ima_client.py check
```

若看到如下输出：
```text
✅ 凭证有效，成功连通腾讯 ima 官方服务！
```
紧接着测试列出知识库：
```bash
python scripts/ima_client.py list
```
即可正常在 AI 助手会话中引用本技能！
