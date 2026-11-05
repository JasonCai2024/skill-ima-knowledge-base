# 常见问题与排障手册 (troubleshooting.md)

本文档整理了调用腾讯 ima.copilot OpenAPI 以及使用 `skill-ima-knowledge-base` 技能时的常见问题与处理方案。

---

## 1. 错误代码速查表

| 错误代码 | 错误消息 | 根本原因 | 解决方案 |
| :---: | :--- | :--- | :--- |
| `200002` | `clientID or apiKey is empty` | 缺少鉴权请求头 | 检查是否正确配置环境变量或 `~/.config/ima/` 凭证文件 |
| `200002` | `skill auth failed` | API Key 失效或过期 | 前往 [ima 接口配置页](https://ima.qq.com/agent-interface) 删除旧凭证并重新生成新 Key |
| `51` | `invalid ... Limit: value must be inside range (0, 20]` | 分页 `limit` 参数超出限制 | 腾讯开放平台硬性限制单次最多查询 20 条，调整 `limit` 在 1~20 之间 |
| `100001` | `ListNoteBook param is error` | 笔记搜索入参格式不合法 | 检查传入的 query 参数结构是否完整 |
| `600001` | `登录过期` | （仅 Cookie 模式触发）Session 过期 | 本技能默认全部采用稳定的 OpenAPI 模式，不依赖 Cookie，不受此错误影响 |

---

## 2. 经典排障场景

### 2.1 报错：未找到有效的腾讯 ima OpenAPI 凭证
- **表现**：运行 CLI 时输出 `ValueError: 未找到有效的腾讯 ima OpenAPI 凭证...`
- **排查步骤**：
  1. 确认是否已在 `~/.config/ima/` 下建立了 `client_id` 和 `api_key` 文件；
  2. Windows 下使用 PowerShell 验证：
     ```powershell
     Get-Content "$HOME\.config\ima\client_id"
     Get-Content "$HOME\.config\ima\api_key"
     ```
  3. 如果使用 `.env`，确认当前执行命令的工作目录或技能根目录下存在 `.env` 文件。

---

### 2.2 报错：200002 skill auth failed
- **表现**：测试探活或调用接口时返回 `IMA API 错误 [200002]: skill auth failed`
- **原因**：腾讯开放平台的 API Key 具有一定时效保护，若长期未调用或在网页端重置过，旧 Key 会失效。
- **解决方案**：
  1. 打开浏览器登录 [https://ima.qq.com/agent-interface](https://ima.qq.com/agent-interface)；
  2. 点击旧凭证旁的「删除」按钮；
  3. 点击「创建凭证」；
  4. 立即将弹窗中的全新 `Client ID` 和 `API Key` 更新到 `~/.config/ima/` 中。

---

### 2.3 上传本地文件时提示同名冲突
- **处理机制**：`ima_client.py` 内部内置了重名探测与自动避让逻辑。
- 当检测到目标知识库根目录已存在同名文件（例如 `架构设计.pdf`）时，工具会自动重命名为 `架构设计_20260926180000.pdf` 并上传，确保上传任务 100% 成功且不覆盖原文件。

---

### 2.4 上传大文件超时
- **原因**：COS 直传默认超时时间为 60 秒。
- **建议**：上传单个文件体积建议在 100MB 以内。超大视频或大模型权重建议拆分或先压缩后再归档。
