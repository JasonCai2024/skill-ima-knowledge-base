---
name: skill-ima-knowledge-base
slug: skill-ima-knowledge-base
displayName: 腾讯IMA知识库管家
version: 1.0.0
summary: 腾讯 ima.copilot 知识库官方 OpenAPI 技能，支持知识库检索、笔记读写、文档直传与文章收录。
license: MIT
description: 腾讯 ima.copilot 知识库操作技能。提供个人与订阅知识库列表浏览、文档及笔记全文检索、读取并提取条目正文、创建 Markdown 笔记、归档笔记到指定知识库、批量收录网页与公众号文章 URL、本地多格式文件直传 COS 入库等全流程功能。当用户需要查询、阅读、提取、写入或归档资料到腾讯 ima 知识库时使用。
disable-model-invocation: true
user-invocable: true
argument-hint: [subcommand-or-query]
---

# 腾讯 ima.copilot 知识库技能说明书

为 AI 编程智能体提供无缝直连腾讯 ima 知识库（ima.copilot）的完整操作能力，彻底摆脱传统 MCP 进程守护与跨工具配置繁琐的问题。

---

## Goal

1. **全面覆盖 ima 官方 OpenAPI 功能**：知识库列表检索、库内全文检索、文档下载与正文预览、笔记读写、文件 COS 直传、URL 批量收录。
2. **零环境侵入与开箱即用**：基于纯 Python 脚本执行，随用随调，不常驻后台，不修改 IDE 深度系统配置。
3. **多层次凭证安全隔离**：优先自适应读取本地 `~/.config/ima/`、环境变量或项目 `.env`，杜绝密钥泄露风险。
4. **智能容错与便捷解析**：支持知识库名称直接解析为 ID，支持重名文件自动加时间戳，支持 Markdown/TXT 格式正文自动提取展示。

---

## Required Inputs

### 1. 运行环境依赖
- **Python**：Python 3.8+（本机已具备 Python 3.12）
- **核心依赖库**：`requests`（`pip install requests`）

### 2. 身份凭证（三选一自动读取）
脚本自动按以下优先级加载鉴权密钥：
1. 命令行参数 `--client-id <ID> --api-key <KEY>`
2. 环境变量 `IMA_CLIENT_ID` / `IMA_API_KEY`（或 `IMA_OPENAPI_*`）
3. 根目录 `.env` 文件
4. 操作系统用户目录 `~/.config/ima/client_id` 与 `~/.config/ima/api_key`

凭证生成入口：[ima 官方开放平台](https://ima.qq.com/agent-interface)

---

## Workflow

AI 助理在收到用户关于 ima 知识库的操作指令时，应在后台通过 `run_command` 执行脚本 `scripts/ima_client.py`，流程如下：

```text
用户提出指令（如“查一下CC工作笔记里的周报”）
  ↓
[Step 1] 意图识别与参数映射
  ├─ 查知识库列表 ──> list
  ├─ 搜库内文档 ────> search "<知识库名或ID>" "<关键词>"
  ├─ 读某篇内容 ────> read "<media_id>"
  ├─ 写新笔记 ──────> create-note "<标题>" "<内容/文件路径>"
  ├─ 存网页/文章 ───> import-urls "<知识库名或ID>" <url1> [url2...]
  └─ 上传本地文件 ──> upload "<知识库名或ID>" "<本地绝对路径>"
  ↓
[Step 2] 调度 Python 脚本执行
  命令模板：python scripts/ima_client.py <subcommand> [args]
  ↓
[Step 3] 解析标准化输出
  若需进一步给用户总结：使用 --format json 获取结构化数据；
  若直接向用户汇报：使用默认 table 格式。
  ↓
[Step 4] 组织友好回复并呈现给用户
```

---

## Decision Rules

1. **知识库标识传参规则**：
   - 知识库参数优先传知识库名称（如 `"CC的工作笔记"`），脚本内部具备自动模糊匹配与 ID 转换机制；
   - 若名称重名或匹配歧义，改传 base64url 格式的精确 ID（以 `=` 结尾）。
2. **分页与数量限制**：
   - 腾讯官方 OpenAPI 对 `search_knowledge_base` 和 `search_knowledge` 的单次 `limit` 严格限制在 `(0, 20]` 区间，超过 20 会触发 51 报错；
   - 脚本内部已做自动限幅截断（`min(limit, 20)`）。如需抓取更多，需利用 `cursor` 迭代请求。
3. **正文预览规则**：
   - 当调用 `read <media_id>` 时：
     - 若为笔记类型（media_type=11），脚本自动级联拉取纯文本内容；
     - 若为 Markdown（media_type=7）或 TXT（media_type=13），脚本自动直接下载正文并在控制台预览；
     - 若为二进制文件（PDF/Word/PPT/Excel/图片），输出带有腾讯云防盗链签名的临时公网下载直链。
4. **上传文件重名规则**：
   - `upload` 命令执行时会自动先调用 `check_repeated_names`；
   - 若发现同名文件，自动追加 `_YYYYMMDDHHMMSS` 时间戳后缀上传，确保不会覆盖或被拦截。

---

## Output Requirements

1. **终端交互**：默认输出对人类可读友好的格式（表格、提示符、带格式的正文预览）。
2. **智能体交互**：若 AI 需要继续处理字段数据，统一追加 `--format json` 参数。
3. **给用户的回复**：AI 需提取有效字段呈现，包含条目名称、所属知识库、关键正文摘录或直接链接，避免裸输出大段报错堆栈。

---

## Validation

在执行具体业务前，可随时运行探活校验命令：

```powershell
python scripts/ima_client.py check
```

- 预期输出：`✅ 凭证有效，成功连通腾讯 ima 官方服务！`
- 若返回 200002：提示用户前往 [ima.qq.com/agent-interface](https://ima.qq.com/agent-interface) 重新刷新 API Key。

---

## Fallback

1. **未找到凭证**：
   - 引导用户在网页端创建凭证，并将密钥写入 `~/.config/ima/client_id` 与 `~/.config/ima/api_key`，或在项目根目录创建 `.env`。
2. **知识库名称不匹配**：
   - 执行 `python scripts/ima_client.py list` 列出全部可用知识库，引导用户核对名称或复制其 ID。
3. **文件上传格式不支持**：
   - 参考 [references/api-reference.md](references/api-reference.md)，支持的文件格式包括：PDF、Word、PPT、Excel、Markdown、图片、TXT、XMind、音频。

---

## Examples

### 示例 1：列出所有知识库
```powershell
python scripts/ima_client.py list
```

### 示例 2：在指定知识库中检索包含“周报”的文档
```powershell
python scripts/ima_client.py search "CC的工作笔记" "周报" --limit 10
```

### 示例 3：读取指定文档正文
```powershell
python scripts/ima_client.py read "markdown_4513c7df4da72fadd9e8583303746616_0a9e6e8bccc38086808c905cf51163537502648009822777"
```

### 示例 4：新建 Markdown 笔记并归档
```powershell
python scripts/ima_client.py create-note "项目复盘纪要" "# 标题\n\n- 完成项A\n- 完成项B"
python scripts/ima_client.py add-note "CC的工作笔记" "<返回的note_id>" "项目复盘纪要"
```

### 示例 5：上传本地文档到知识库
```powershell
python scripts/ima_client.py upload "CC的工作笔记" "E:\Docs\架构设计方案.pdf"
```

### 示例 6：一键批量收录优质文章 URL
```powershell
python scripts/ima_client.py import-urls "自媒体创作" "https://mp.weixin.qq.com/s/xxxxxx"
```
