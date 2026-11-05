# skill-ima-knowledge-base

> **公开 GitHub 仓库直链**：<https://github.com/JasonCai2024/skill-ima-knowledge-base.git>  
> **一键克隆指令**：
> ```bash
> git clone https://github.com/JasonCai2024/skill-ima-knowledge-base.git
> ```

---

## 一、 项目简介与技能定位

`skill-ima-knowledge-base` 是专为 AI 编程智能体（Claude Code、Antigravity、OpenClaw、Codex 等）打造的**腾讯 ima.copilot 知识库官方 OpenAPI 自动化技能**。它通过轻量、自包含的 Python 工具链，完全覆盖了原有 ima-mcp-server 的全部功能，赋予 AI 助理“随时随地、即调即走”的知识库读写与管理能力。

### 🌟 3 大核心卖点
1. **彻底告别 MCP 繁琐配置**：无需在 IDE 配置文件（如 `mcp_config.json`）中手动写入 JSON，无需后台挂载 Node.js 常驻守护进程，零内存开销，开箱即用。
2. **全功能能力矩阵覆盖**：涵盖知识库列表查阅、库内文件检索、正文纯文本自动提取、Markdown 笔记创建、URL 网页收录以及腾讯云 COS 签名直传文件。
3. **极简迁移与多环境适配**：只要具备 Python 3.8+ 环境，无论在 Windows、macOS 还是 Linux 终端中，把本技能目录放入智能体体系即可直接驱动。

---

## 二、 架构与数据流转图

```mermaid
flowchart TD
    User([用户自然语言指令]) --> Agent[AI 编程智能体 (Antigravity / Claude Code)]
    Agent -->|根据 SKILL.md 决策| CLI["scripts/ima_client.py"]
    
    subgraph AuthLayer [凭证自适应层]
        CLI -.->|优先级 1| Arg[命令行参数]
        CLI -.->|优先级 2| Env[环境变量 IMA_CLIENT_ID / KEY]
        CLI -.->|优先级 3| DotEnv[项目根目录 .env]
        CLI -.->|优先级 4| LocalConfig["~/.config/ima/ 凭证文件"]
    end

    CLI -->|HTTPS POST| TencentAPI["腾讯 ima 官方开放平台 (ima.qq.com/openapi)"]
    
    subgraph TencentServices [腾讯云端服务]
        TencentAPI --> Wiki["wiki/v1 (知识库/搜索/URL导入)"]
        TencentAPI --> Note["note/v1 (Markdown笔记读写)"]
        TencentAPI --> COS["腾讯云 COS 对象存储 (文档直传)"]
    end

    TencentServices -->|JSON / 正文数据流| CLI
    CLI -->|格式化表格 / JSON 结果| Agent
    Agent --> Final([最终分析报告 / 回答结果呈现给用户])
```

---

## 三、 获取与安装配置

### 1. 环境依赖
- **Python**：Python 3.8+（推荐 Python 3.10+）
- **核心包**：`requests`

```bash
pip install requests
```

### 2. 凭证配置（三选一）
前往 [腾讯 ima 开放平台](https://ima.qq.com/agent-interface) 登录并点击“创建凭证”，获取 `Client ID` 和 `API Key`：

- **方式 A（全局推荐）**：存入用户主目录凭证文件（不会被任何 Git 误提交）
  - Linux/macOS: `~/.config/ima/client_id` 与 `~/.config/ima/api_key`
  - Windows: `C:\Users\<用户名>\.config\ima\client_id` 与 `api_key`
- **方式 B（项目隔离）**：复制本目录的 `.env.example` 为 `.env` 并填入：
  ```bash
  IMA_CLIENT_ID="你的_Client_ID"
  IMA_API_KEY="你的_API_Key"
  ```
- **方式 C（环境变量）**：
  ```bash
  export IMA_CLIENT_ID="你的_Client_ID"
  export IMA_API_KEY="你的_API_Key"
  ```

### 3. 一键健康探活
在终端中执行以下命令验证连通性：

```bash
python scripts/ima_client.py check
```
> 输出 `✅ 凭证有效，成功连通腾讯 ima 官方服务！` 即表示准备完毕。

---

## 四、 使用说明

### 1. 能做什么与怎么对 AI 助理说

AI 助理加载本技能后，你可以直接使用自然语言吩咐它。以下是典型指令与底层执行命令的对照表：

| 业务能力 | 你可以对 AI 助理说的自然语言指令 | 底层 CLI 执行命令 |
| :--- | :--- | :--- |
| **连通检查** | “检查一下我与腾讯 ima 知识库的连接状态” | `python scripts/ima_client.py check` |
| **知识库列表** | “列出我账号下所有的 ima 知识库” | `python scripts/ima_client.py list` |
| **库内搜索** | “在 CC的工作笔记 知识库里搜一下关于‘项目’的文档” | `python scripts/ima_client.py search "CC的工作笔记" "项目"` |
| **文档阅读** | “帮我读取 media_id 为 markdown_xxxx 的文档正文” | `python scripts/ima_client.py read "<media_id>"` |
| **读取笔记** | “提取 note_id 为 123456 的纯文本笔记内容” | `python scripts/ima_client.py read-note "<note_id>"` |
| **新建笔记** | “在 ima 中创建一篇标题为‘会议纪要’的 Markdown 笔记” | `python scripts/ima_client.py create-note "会议纪要" "# 正文内容..."` |
| **笔记归档** | “把刚刚创建的笔记添加到‘CC的迭代笔记’知识库中” | `python scripts/ima_client.py add-note "CC的迭代笔记" "<note_id>" "会议纪要"` |
| **上传文档** | “把当前目录的‘2026架构规划.pdf’上传归档到 CC的工作笔记” | `python scripts/ima_client.py upload "CC的工作笔记" "./2026架构规划.pdf"` |
| **收录网页** | “将这篇公众号文章收录进‘自媒体创作’知识库：https://mp.weixin.qq.com/...” | `python scripts/ima_client.py import-urls "自媒体创作" "https://..."` |
| **权限查询** | “查一下我有哪些 ima 知识库具备写入权限” | `python scripts/ima_client.py list-addable` |

---

### 2. 典型实战场景工作流

#### 场景 1：历史周报与项目工作检索
1. **指令**：“帮我检索‘CC的工作笔记’知识库里关于 2026 年 6 月份的周报，并总结 6 月中旬的主要工作。”
2. **AI 执行**：
   ```bash
   python scripts/ima_client.py search "CC的工作笔记" "202606"
   python scripts/ima_client.py read "markdown_4513c7df4da72fadd9e8583303746616_0a9e6e8bccc38086808c905cf51163537502648009822777"
   ```
3. **结果**：AI 自动完成检索、拉取正文、阅读分析，提炼出周度重点汇报内容。

#### 场景 2：代码评审记录一键生成并沉淀入库
1. **指令**：“把刚才我们讨论生成的《重构决策清单》整理成一篇 Markdown 笔记，并保存到我的‘CC的迭代笔记’知识库。”
2. **AI 执行**：
   ```bash
   python scripts/ima_client.py create-note "2026-09重构决策清单" "# 重构清单\n- 模块A解耦\n- 统一API错误码"
   python scripts/ima_client.py add-note "CC的迭代笔记" "<返回的doc_id>" "2026-09重构决策清单"
   ```
3. **结果**：笔记直接出现在用户的云端 ima 知识库中。

#### 场景 3：微信公众号/技术文章一键批量收集
1. **指令**：“帮我把这 3 篇 AI 技术文章存到‘自媒体创作’知识库里。”
2. **AI 执行**：
   ```bash
   python scripts/ima_client.py import-urls "自媒体创作" "https://mp.weixin.qq.com/s/1" "https://mp.weixin.qq.com/s/2"
   ```
3. **结果**：ima 云端异步完成抓取并纳入检索体系。

---

## 五、 凭证安全与隔离规范

1. **零敏感数据硬编码**：本仓库代码中绝对不包含任何明文 `Client ID`、`API Key` 或任何测试凭据。
2. **严格的 `.gitignore` 保护**：仓库默认忽略所有 `.env` 文件、本地生成的临时媒体、日志以及凭证缓存。
3. **官方网络隔离原则**：脚本发起的所有 HTTPS 网络请求**严格仅发送给腾讯官方指定域名**（`https://ima.qq.com` 与 `*.cos.<region>.myqcloud.com`），绝不向任何第三方转发凭据。

---

## 六、 文件目录结构与核心设计决策

```text
skill-ima-knowledge-base/
├── SKILL.md                     # Claude Code / 智能体规范技能定义文件
├── README.md                    # 项目核心说明书与架构总览（本文件）
├── INSTALL.md                   # 详细部署与环境初始化指南
├── CHANGELOG.md                 # 遵循 Keep a Changelog 规范的版本演进记录
├── .env.example                 # 环境变量模板文件
├── .gitignore                   # Git 忽略规则
├── scripts/
│   └── ima_client.py            # 核心 CLI 实现（包含 HMAC-SHA1 COS 直传、API 封装与智能解析）
└── references/
    ├── api-reference.md         # 腾讯 ima OpenAPI 接口参数速查参考
    └── troubleshooting.md       # 常见错误代码（200002/51等）与排障手册
```

### 核心设计决策
- **为什么选择原生 Python CLI 而非 MCP Server？**
  对于现代具备终端能力的 AI 编程工具，调用 Python 脚本比维护 JSON-RPC Stdio 守护进程更可靠。随用随开、轻量高效，同时可以借助 Git 将整个技能跨机自由漫游。
- **智能名称反查机制**：
  用户平时只记得“CC的工作笔记”这样的人类语言名称，记不住一长串 base64 ID。脚本内部实现了自动探测与双向匹配，大幅提升人机交互体验。
- **纯 Python 原生 COS 签名实现**：
  不依赖体积臃肿的 `cos-python-sdk-v5`，仅用 Python 标准库 `hmac` + `hashlib` 计算符合腾讯云 COS V5 规范的签名，保持依赖极简纯净。

---

## 七、 许可证

本项目遵循 [MIT License](LICENSE) 授权许可。
