# 腾讯 ima OpenAPI 接口参数速查参考

本文档记录腾讯 ima.copilot 官方 OpenAPI 的底层端点协议规范，供开发者与 AI 助理参考。

---

## 1. 基础规范

- **基础 URL**：`https://ima.qq.com`
- **请求方式**：所有 OpenAPI 接口均采用 `POST` 方法。
- **请求头规范**：
  ```http
  ima-openapi-clientid: <Client ID>
  ima-openapi-apikey: <API Key>
  ima-openapi-ctx: cli_version=1.0.0
  Content-Type: application/json
  ```
- **统一响应结构**：
  ```json
  {
    "code": 0,
    "msg": "success",
    "data": { ... },
    "request_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
  ```

---

## 2. 核心端点明细

### 2.1 知识库模块 (`openapi/wiki/v1/`)

#### 1. `search_knowledge_base`（获取/搜索知识库列表）
- **路径**：`POST /openapi/wiki/v1/search_knowledge_base`
- **请求体**：
  ```json
  {
    "query": "",
    "cursor": "",
    "limit": 20
  }
  ```
- **注意事项**：`limit` 必须在区间 `(0, 20]`，超过 20 会触发错误代码 51。
- **返回字段**：
  - `data.info_list`: 知识库列表数组。包含 `kb_id`, `kb_name`, `creator`, `role_type`, `base_type`, `content_count`。

#### 2. `get_knowledge_base`（获取指定知识库元数据）
- **路径**：`POST /openapi/wiki/v1/get_knowledge_base`
- **请求体**：
  ```json
  {
    "ids": ["<kb_id>"]
  }
  ```
- **返回字段**：
  - `data.infos`: 以 `<kb_id>` 为键的对象，包含名称、封面、描述等。

#### 3. `search_knowledge`（检索知识库内条目）
- **路径**：`POST /openapi/wiki/v1/search_knowledge`
- **请求体**：
  ```json
  {
    "knowledge_base_id": "<kb_id>",
    "query": "关键词",
    "cursor": "",
    "limit": 20
  }
  ```
- **返回字段**：
  - `data.info_list`: 匹配条目列表。包含 `media_id`, `title`, `media_type`, `parent_folder_id`。

#### 4. `get_media_info`（获取条目内容/直链）
- **路径**：`POST /openapi/wiki/v1/get_media_info`
- **请求体**：
  ```json
  {
    "media_id": "<media_id>"
  }
  ```
- **返回字段**：
  - `data.url_info.url`: 文件下载或访问直链（包含防盗链时间戳与签名）。
  - `data.notebook_ext_info.notebook_id`: 若为笔记条目，由此 ID 可级联拉取纯文本内容。

#### 5. `import_urls`（批量导入网页/公众号链接）
- **路径**：`POST /openapi/wiki/v1/import_urls`
- **请求体**：
  ```json
  {
    "knowledge_base_id": "<kb_id>",
    "urls": ["https://..."],
    "folder_id": "folder_xxx" (可选)
  }
  ```

#### 6. `check_repeated_names`（探测同名文件）
- **路径**：`POST /openapi/wiki/v1/check_repeated_names`
- **请求体**：
  ```json
  {
    "knowledge_base_id": "<kb_id>",
    "params": [
      {"name": "file.pdf", "media_type": 1}
    ]
  }
  ```

#### 7. `create_media`（申请创建媒体并获取 COS 上传临时凭据）
- **路径**：`POST /openapi/wiki/v1/create_media`
- **请求体**：
  ```json
  {
    "file_name": "filename.ext",
    "file_size": 1024,
    "content_type": "application/pdf",
    "knowledge_base_id": "<kb_id>",
    "file_ext": "pdf"
  }
  ```
- **返回字段**：
  - `data.media_id`
  - `data.cos_credential`: 包含 `secret_id`, `secret_key`, `token`, `cos_key`, `bucket`, `region` 等。

#### 8. `add_knowledge`（文件/笔记登记到知识库）
- **路径**：`POST /openapi/wiki/v1/add_knowledge`
- **请求体**：
  ```json
  {
    "media_type": 1,
    "media_id": "<media_id>",
    "title": "filename.pdf",
    "knowledge_base_id": "<kb_id>",
    "file_info": {
      "cos_key": "<cos_key>",
      "file_size": 1024,
      "file_name": "filename.pdf"
    }
  }
  ```

---

### 2.2 笔记模块 (`openapi/note/v1/`)

#### 1. `import_doc`（创建 Markdown 笔记）
- **路径**：`POST /openapi/note/v1/import_doc`
- **请求体**：
  ```json
  {
    "content_format": 1,
    "content": "# 标题\n\n正文内容"
  }
  ```
- **返回字段**：
  - `data.doc_id`: 笔记全局唯一标识。

#### 2. `get_doc_content`（获取笔记正文）
- **路径**：`POST /openapi/note/v1/get_doc_content`
- **请求体**：
  ```json
  {
    "note_id": "<note_id>",
    "target_content_format": 0
  }
  ```
- **返回字段**：
  - `data.content`: 笔记纯文本或富文本正文。

---

## 3. 常见 Media Type 字典

| media_type | 对应文件类型 / 格式 |
| :---: | :--- |
| `1` | PDF (`.pdf`) |
| `3` | Word (`.doc`, `.docx`) |
| `4` | PPT (`.ppt`, `.pptx`) |
| `5` | Excel (`.xls`, `.xlsx`, `.csv`) |
| `7` | Markdown (`.md`, `.markdown`) |
| `9` | 图片 (`.png`, `.jpg`, `.jpeg`, `.webp`) |
| `11` | IMA 云端笔记条目 |
| `13` | 纯文本 (`.txt`) |
| `14` | XMind 思维导图 (`.xmind`) |
| `15` | 音频 (`.mp3`, `.m4a`, `.wav`, `.aac`) |
