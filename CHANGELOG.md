# Changelog

本文件记录本技能（skill-ima-knowledge-base）的所有用户可见变更。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增
- 计划支持流式输出增强。
- 计划支持批量多文件并行直传优化。

## [1.0.0] - 2026-09-26

### 新增
- 初始版本发布，全面实现腾讯 ima 知识库官方 OpenAPI 能力。
- `scripts/ima_client.py` 核心命令行工具，提供 12 项原子能力：
  - `check`：探活与凭证有效性检查；
  - `list`：列出个人与订阅知识库；
  - `get-kb`：获取指定知识库元数据；
  - `search`：知识库内文档、笔记、文件检索；
  - `read`：获取条目下载直链，Markdown/TXT 正文自动拉取预览；
  - `read-note`：读取笔记正文纯文本；
  - `create-note`：创建 Markdown 格式的云端笔记；
  - `add-note`：将已有笔记归档到指定知识库；
  - `import-urls`：批量添加网页与微信公众号链接；
  - `check-names`：上传前同名文件重复探测；
  - `upload`：本地文件直传腾讯云 COS 存储桶并登记入库；
  - `list-addable`：获取具备写入权限的知识库列表。
- 原生 HMAC-SHA1 腾讯云 COS 上传签名实现，零第三方臃肿 SDK 依赖。
- 智能知识库名称自动解析与模糊匹配。
- 多优先级凭证自动加载机制（CLI > ENV > .env > ~/.config/ima/）。
- 详尽文档体系：`SKILL.md`、`README.md`、`INSTALL.md`、`references/` 规范参考。

[Unreleased]: https://github.com/JasonCai2024/skill-ima-knowledge-base
[1.0.0]: https://github.com/JasonCai2024/skill-ima-knowledge-base/releases/tag/v1.0.0
