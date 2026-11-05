#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tencent IMA Knowledge Base Client (ima_client.py)
面向 AI 编程智能体的腾讯 ima.copilot 知识库官方 OpenAPI 命令行工具。
完全覆盖 IMA 知识库所有核心能力（搜、读、写、传、归档）。
"""

import os
import sys
import json
import time
import hmac
import hashlib
import argparse
from pathlib import Path
from urllib.parse import quote
import requests

BASE_URL = "https://ima.qq.com"
API_PREFIX = "openapi/wiki/v1"
NOTE_PREFIX = "openapi/note/v1"
CLIENT_VERSION = "1.0.0"

# 常见文件扩展名到 media_type 与 content_type 的映射
FILE_TYPE_MAP = {
    "pdf":   {"media_type": 1,  "content_type": "application/pdf"},
    "doc":   {"media_type": 3,  "content_type": "application/msword"},
    "docx":  {"media_type": 3,  "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "ppt":   {"media_type": 4,  "content_type": "application/vnd.ms-powerpoint"},
    "pptx":  {"media_type": 4,  "content_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    "xls":   {"media_type": 5,  "content_type": "application/vnd.ms-excel"},
    "xlsx":  {"media_type": 5,  "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    "csv":   {"media_type": 5,  "content_type": "text/csv"},
    "md":    {"media_type": 7,  "content_type": "text/markdown"},
    "markdown": {"media_type": 7, "content_type": "text/markdown"},
    "png":   {"media_type": 9,  "content_type": "image/png"},
    "jpg":   {"media_type": 9,  "content_type": "image/jpeg"},
    "jpeg":  {"media_type": 9,  "content_type": "image/jpeg"},
    "webp":  {"media_type": 9,  "content_type": "image/webp"},
    "txt":   {"media_type": 13, "content_type": "text/plain"},
    "xmind": {"media_type": 14, "content_type": "application/x-xmind"},
    "mp3":   {"media_type": 15, "content_type": "audio/mpeg"},
    "m4a":   {"media_type": 15, "content_type": "audio/mp4"},
    "wav":   {"media_type": 15, "content_type": "audio/wav"},
    "aac":   {"media_type": 15, "content_type": "audio/aac"},
}


def load_env_file(dotenv_path=None):
    """尝试加载 .env 文件中的键值对"""
    paths_to_check = []
    if dotenv_path:
        paths_to_check.append(Path(dotenv_path))
    paths_to_check.extend([
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent / ".env"
    ])
    for p in paths_to_check:
        if p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
                break
            except Exception:
                pass


def load_credentials(explicit_client_id=None, explicit_api_key=None):
    """
    按优先级读取凭证：
    1. 显式传入参数
    2. 环境变量 (IMA_CLIENT_ID / IMA_API_KEY 或 IMA_OPENAPI_*)
    3. 本地 .env 文件
    4. ~/.config/ima/ 目录下的 client_id 与 api_key
    """
    client_id = explicit_client_id or os.environ.get("IMA_CLIENT_ID") or os.environ.get("IMA_OPENAPI_CLIENTID")
    api_key = explicit_api_key or os.environ.get("IMA_API_KEY") or os.environ.get("IMA_OPENAPI_APIKEY")

    if not client_id or not api_key:
        load_env_file()
        client_id = client_id or os.environ.get("IMA_CLIENT_ID") or os.environ.get("IMA_OPENAPI_CLIENTID")
        api_key = api_key or os.environ.get("IMA_API_KEY") or os.environ.get("IMA_OPENAPI_APIKEY")

    if not client_id or not api_key:
        cfg_dir = Path.home() / ".config" / "ima"
        cid_file = cfg_dir / "client_id"
        key_file = cfg_dir / "api_key"
        if cid_file.is_file() and not client_id:
            try:
                client_id = cid_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass
        if key_file.is_file() and not api_key:
            try:
                api_key = key_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass

    if not client_id or not api_key:
        raise ValueError(
            "未找到有效的腾讯 ima OpenAPI 凭证。\n"
            "请前往 https://ima.qq.com/agent-interface 创建凭证，并配置为：\n"
            "1. 环境变量 IMA_CLIENT_ID 与 IMA_API_KEY；\n"
            "2. 项目根目录 .env 文件；\n"
            "3. 本地配置文件 ~/.config/ima/client_id 与 ~/.config/ima/api_key。"
        )

    return client_id, api_key


class ImaClient:
    def __init__(self, client_id=None, api_key=None):
        self.client_id, self.api_key = load_credentials(client_id, api_key)
        self.session = requests.Session()

    def _request(self, endpoint, payload=None, prefix=API_PREFIX, timeout=30):
        url = f"{BASE_URL}/{prefix}/{endpoint}"
        headers = {
            "ima-openapi-clientid": self.client_id,
            "ima-openapi-apikey": self.api_key,
            "ima-openapi-ctx": f"cli_version={CLIENT_VERSION}",
            "Content-Type": "application/json",
        }
        res = self.session.post(url, json=payload or {}, headers=headers, timeout=timeout)
        try:
            data = res.json()
        except Exception:
            raise RuntimeError(f"IMA API 返回非 JSON 格式响应 (HTTP {res.status_code}): {res.text[:200]}")

        code = data.get("code")
        if code != 0:
            msg = data.get("msg", "未知错误")
            raise RuntimeError(f"IMA API 错误 [{code}]: {msg} (request_id: {data.get('request_id', '')})")

        return data.get("data", {})

    def check_credentials(self):
        """测试凭证有效性"""
        try:
            self._request("search_knowledge_base", {"query": "", "cursor": "", "limit": 1})
            return {"valid": True, "message": "凭证有效，连接正常"}
        except Exception as e:
            return {"valid": False, "message": str(e)}

    def list_knowledge_bases(self, query="", limit=20, cursor=""):
        """获取用户拥有的知识库列表"""
        payload = {
            "query": query or "",
            "cursor": cursor or "",
            "limit": min(max(1, int(limit)), 20)
        }
        data = self._request("search_knowledge_base", payload)
        return data.get("info_list", [])

    def get_knowledge_base(self, kb_id):
        """获取指定知识库详情"""
        data = self._request("get_knowledge_base", {"ids": [kb_id]})
        infos = data.get("infos", {})
        return infos.get(kb_id, {})

    def resolve_kb_id(self, kb_id_or_name):
        """如果传入的是名称，自动搜索匹配解析成 ID"""
        if not kb_id_or_name:
            kb_list = self.list_knowledge_bases(limit=5)
            if len(kb_list) == 1:
                return kb_list[0].get("kb_id")
            elif not kb_list:
                raise ValueError("当前账号下没有任何可用的知识库，请先前往 ima.qq.com 创建")
            else:
                names = [f"  - {kb.get('kb_name')} (ID: {kb.get('kb_id')})" for kb in kb_list]
                raise ValueError("检测到多个知识库，请指定 --kb-id：\n" + "\n".join(names))

        # 检查是否本身就是有效 ID（base64url 格式以 = 结尾且长度 >= 30）
        if kb_id_or_name.endswith("=") and len(kb_id_or_name) >= 30:
            return kb_id_or_name

        # 名称模糊匹配
        kb_list = self.list_knowledge_bases(limit=20)
        target = kb_id_or_name.strip().lower()
        exact_matches = [kb for kb in kb_list if kb.get("kb_name", "").strip().lower() == target]
        if exact_matches:
            return exact_matches[0].get("kb_id")

        partial_matches = [kb for kb in kb_list if target in kb.get("kb_name", "").strip().lower()]
        if len(partial_matches) == 1:
            return partial_matches[0].get("kb_id")
        elif len(partial_matches) > 1:
            names = [f"  - {kb.get('kb_name')} (ID: {kb.get('kb_id')})" for kb in partial_matches]
            raise ValueError(f"关键词 '{kb_id_or_name}' 匹配到多个知识库，请指定完整名称或 ID：\n" + "\n".join(names))

        raise ValueError(f"未找到名称匹配 '{kb_id_or_name}' 的知识库")

    def search_knowledge(self, kb_id, query="", limit=20, cursor=""):
        """在知识库内检索文档/笔记/文件"""
        actual_kb_id = self.resolve_kb_id(kb_id)
        payload = {
            "knowledge_base_id": actual_kb_id,
            "query": query or "",
            "cursor": cursor or "",
            "limit": min(max(1, int(limit)), 20)
        }
        data = self._request("search_knowledge", payload)
        return data.get("info_list", [])

    def get_media_info(self, media_id):
        """获取条目正文或下载链接"""
        data = self._request("get_media_info", {"media_id": media_id})
        # 若是笔记条目，自动级联读取正文
        ext_info = data.get("notebook_ext_info") or {}
        note_id = ext_info.get("notebook_id")
        if note_id:
            try:
                note_doc = self.get_note_content(str(note_id))
                data["note_content"] = note_doc.get("content", "")
            except Exception as e:
                data["note_content_error"] = str(e)
        return data

    def get_note_content(self, note_id, target_format=0):
        """读取笔记正文（0=纯文本）"""
        payload = {
            "note_id": str(note_id),
            "target_content_format": target_format
        }
        return self._request("get_doc_content", payload, prefix=NOTE_PREFIX)

    def create_note(self, title, content, folder_name=None):
        """创建一篇 IMA 笔记（支持 Markdown）"""
        md_text = f"# {title}\n\n{content}" if title else content
        payload = {
            "content_format": 1,  # Markdown 格式
            "content": md_text
        }
        if folder_name:
            payload["folder_name"] = folder_name
        return self._request("import_doc", payload, prefix=NOTE_PREFIX)

    def add_note_to_knowledge_base(self, kb_id, note_id, title, folder_id=None):
        """将已有笔记收录到指定知识库"""
        actual_kb_id = self.resolve_kb_id(kb_id)
        payload = {
            "media_type": 11,
            "note_info": {"content_id": str(note_id)},
            "title": title,
            "knowledge_base_id": actual_kb_id
        }
        if folder_id:
            payload["folder_id"] = folder_id
        return self._request("add_knowledge", payload)

    def import_urls(self, kb_id, urls, folder_id=None):
        """将网页或公众号文章链接批量导入知识库"""
        actual_kb_id = self.resolve_kb_id(kb_id)
        if isinstance(urls, str):
            urls = [urls]
        payload = {
            "knowledge_base_id": actual_kb_id,
            "urls": urls[:10]  # 单次限制最多10个
        }
        if folder_id:
            payload["folder_id"] = folder_id
        return self._request("import_urls", payload)

    def get_addable_knowledge_base_list(self, limit=20, cursor=""):
        """获取当前账号有写入/添加权限的知识库"""
        payload = {
            "cursor": cursor or "",
            "limit": min(limit, 50)
        }
        return self._request("get_addable_knowledge_base_list", payload)

    def check_repeated_names(self, kb_id, file_path_or_names, folder_id=None):
        """检查知识库根目录或指定文件夹下是否存在重名文件"""
        actual_kb_id = self.resolve_kb_id(kb_id)
        params = []
        for item in file_path_or_names:
            if isinstance(item, dict):
                params.append(item)
            else:
                p = Path(item)
                ext = p.suffix.lstrip(".").lower()
                media_type = FILE_TYPE_MAP.get(ext, {}).get("media_type", 13)
                params.append({"name": p.name, "media_type": media_type})

        payload = {
            "params": params,
            "knowledge_base_id": actual_kb_id
        }
        if folder_id:
            payload["folder_id"] = folder_id
        data = self._request("check_repeated_names", payload)
        return data.get("results", [])

    def upload_file(self, kb_id, file_path, folder_id=None):
        """
        上传本地文件到知识库：
        1. 校验本地文件并解析媒体类型
        2. 自动检查重名，若重名自动追加时间戳后缀
        3. 调用 create_media 获取腾讯云 COS 临时上传凭证
        4. 使用 HMAC-SHA1 签名直接 PUT 上传到 COS 存储桶
        5. 调用 add_knowledge 登记到知识库
        """
        actual_kb_id = self.resolve_kb_id(kb_id)
        path_obj = Path(file_path).resolve()
        if not path_obj.is_file():
            raise FileNotFoundError(f"本地文件不存在: {file_path}")

        ext = path_obj.suffix.lstrip(".").lower()
        if ext not in FILE_TYPE_MAP:
            supported = ", ".join(FILE_TYPE_MAP.keys())
            raise ValueError(f"不支持的文件后缀 .{ext}，支持类型：{supported}")

        type_meta = FILE_TYPE_MAP[ext]
        media_type = type_meta["media_type"]
        content_type = type_meta["content_type"]
        file_size = path_obj.stat().st_size

        if file_size == 0:
            raise ValueError("待上传文件为空文件 (0 字节)")

        file_name = path_obj.name

        # 1. 检查重名
        check_res = self.check_repeated_names(actual_kb_id, [path_obj], folder_id=folder_id)
        if check_res and check_res[0].get("is_repeated"):
            ts = time.strftime("%Y%m%d%H%M%S")
            stem = path_obj.stem
            file_name = f"{stem}_{ts}.{ext}"

        # 2. 创建媒体获取 COS 凭证
        create_payload = {
            "file_name": file_name,
            "file_size": file_size,
            "content_type": content_type,
            "knowledge_base_id": actual_kb_id,
            "file_ext": ext
        }
        create_res = self._request("create_media", create_payload)
        media_id = create_res.get("media_id")
        cos_cred = create_res.get("cos_credential")
        if not cos_cred:
            raise RuntimeError(f"create_media 未返回 COS 上传凭证: {create_res}")

        # 3. 上传到 COS
        self._upload_to_cos(cos_cred, path_obj, content_type)

        # 4. 登记注册到知识库
        add_payload = {
            "media_type": media_type,
            "media_id": media_id,
            "title": file_name,
            "knowledge_base_id": actual_kb_id,
            "file_info": {
                "cos_key": cos_cred.get("cos_key"),
                "file_size": file_size,
                "file_name": file_name
            }
        }
        if folder_id:
            add_payload["folder_id"] = folder_id

        add_res = self._request("add_knowledge", add_payload)
        return {
            "success": True,
            "file_name": file_name,
            "media_id": add_res.get("media_id") or media_id,
            "knowledge_base_id": actual_kb_id,
            "message": f"文件「{file_name}」已成功上传并归档至知识库"
        }

    def _upload_to_cos(self, cos_cred, file_path_obj, content_type):
        """腾讯云 COS 签名与直传实现"""
        secret_id = cos_cred.get("secret_id")
        secret_key = cos_cred.get("secret_key")
        token = cos_cred.get("token")
        bucket = cos_cred.get("bucket") or cos_cred.get("bucket_name")
        region = cos_cred.get("region")
        cos_key = cos_cred.get("cos_key")

        host = f"{bucket}.cos.{region}.myqcloud.com"
        now = int(time.time())
        start = now - 60
        end = now + 3600
        key_time = f"{start};{end}"

        # 计算签名密钥
        sign_key = hmac.new(secret_key.encode("utf-8"), key_time.encode("utf-8"), hashlib.sha1).hexdigest()

        http_method = "put"
        http_uri = "/" + cos_key.lstrip("/")
        query_string = ""
        header_list = "content-type;host"
        ct_encoded = quote(content_type, safe="")
        host_encoded = quote(host, safe="")
        header_string = f"content-type={ct_encoded}&host={host_encoded}"
        http_string = f"{http_method}\n${http_uri}\n${query_string}\n${header_string}\n"

        http_sha1 = hashlib.sha1(http_string.encode("utf-8")).hexdigest()
        string_to_sign = f"sha1\n{key_time}\n{http_sha1}\n"
        signature = hmac.new(sign_key.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1).hexdigest()

        authorization = (
            f"q-sign-algorithm=sha1&q-ak={secret_id}&q-sign-time={key_time}"
            f"&q-key-time={key_time}&q-header-list={header_list}&q-url-param-list=&q-signature={signature}"
        )

        with open(file_path_obj, "rb") as f:
            file_data = f.read()

        put_url = f"https://{host}{http_uri}"
        put_headers = {
            "Host": host,
            "Content-Type": content_type,
            "Content-Length": str(len(file_data)),
            "Authorization": authorization,
            "x-cos-security-token": token,
        }

        put_res = requests.put(put_url, data=file_data, headers=put_headers, timeout=60)
        if put_res.status_code != 200:
            raise RuntimeError(f"COS 直传失败 (HTTP {put_res.status_code}): {put_res.text[:300]}")


# ──────────────────────────────────────────────────────────────
# 命令行 CLI 入口
# ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="ima_client.py",
        description="腾讯 ima.copilot 知识库官方 OpenAPI 命令行交互工具"
    )
    parser.add_argument("--client-id", help="IMA OpenAPI Client ID")
    parser.add_argument("--api-key", help="IMA OpenAPI API Key")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="输出格式（默认 table）")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 1. 探活检查
    subparsers.add_parser("check", help="检查凭证有效性与连通性")

    # 2. 列出知识库
    p_list = subparsers.add_parser("list", help="列出账号下的知识库")
    p_list.add_argument("--query", "-q", default="", help="搜索过滤词")
    p_list.add_argument("--limit", "-l", type=int, default=20, help="数量上限（默认20）")

    # 3. 知识库详情
    p_get_kb = subparsers.add_parser("get-kb", help="获取指定知识库详情")
    p_get_kb.add_argument("kb_id", help="知识库 ID 或名称")

    # 4. 搜索知识库文档
    p_search = subparsers.add_parser("search", help="检索指定知识库中的文档或笔记")
    p_search.add_argument("kb_id", help="知识库 ID 或名称")
    p_search.add_argument("query", nargs="?", default="", help="搜索关键词（省略则列出最新条目）")
    p_search.add_argument("--limit", "-l", type=int, default=20, help="返回条数（默认20）")

    # 5. 读取条目正文/下载链接
    p_read = subparsers.add_parser("read", help="根据 media_id 获取条目正文或下载链接")
    p_read.add_argument("media_id", help="条目 media_id")

    # 6. 读取笔记正文
    p_read_note = subparsers.add_parser("read-note", help="根据 note_id 读取笔记纯文本正文")
    p_read_note.add_argument("note_id", help="笔记数字 ID")

    # 7. 创建笔记
    p_note = subparsers.add_parser("create-note", help="创建一篇 Markdown 笔记")
    p_note.add_argument("title", help="笔记标题")
    p_note.add_argument("content", help="Markdown 正文内容或文件路径")
    p_note.add_argument("--folder", help="笔记所在文件夹名称")

    # 8. 归档笔记到知识库
    p_add_note = subparsers.add_parser("add-note", help="将已创建的笔记添加到知识库")
    p_add_note.add_argument("kb_id", help="目标知识库 ID 或名称")
    p_add_note.add_argument("note_id", help="笔记数字 ID")
    p_add_note.add_argument("title", help="知识库中显示的标题")

    # 9. 导入网页 URL
    p_import = subparsers.add_parser("import-urls", help="添加网页/公众号文章 URL 到知识库")
    p_import.add_argument("kb_id", help="目标知识库 ID 或名称")
    p_import.add_argument("urls", nargs="+", help="网页链接列表（1-10个）")

    # 10. 上传本地文件
    p_upload = subparsers.add_parser("upload", help="上传本地文件到知识库")
    p_upload.add_argument("kb_id", help="目标知识库 ID 或名称")
    p_upload.add_argument("file_path", help="本地文件绝对路径")
    p_upload.add_argument("--folder-id", help="目标文件夹 ID")

    # 11. 检查重名
    p_check_names = subparsers.add_parser("check-names", help="检查知识库中是否存在重名文件")
    p_check_names.add_argument("kb_id", help="目标知识库 ID 或名称")
    p_check_names.add_argument("files", nargs="+", help="待检查的文件路径或文件名")

    # 12. 列出可写入知识库
    subparsers.add_parser("list-addable", help="列出当前具备写入权限的知识库")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        client = ImaClient(args.client_id, args.api_key)
    except Exception as e:
        print(f"❌ 认证初始化失败: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.command == "check":
            res = client.check_credentials()
            if args.format == "json":
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                if res["valid"]:
                    print("✅ 凭证有效，成功连通腾讯 ima 官方服务！")
                else:
                    print(f"❌ 连通失败: {res['message']}")

        elif args.command == "list":
            kbs = client.list_knowledge_bases(query=args.query, limit=args.limit)
            if args.format == "json":
                print(json.dumps(kbs, ensure_ascii=False, indent=2))
            else:
                print(f"📚 找到 {len(kbs)} 个知识库：\n")
                print(f"{'名称':<28} | {'类型':<12} | {'文档数':<6} | {'ID'}")
                print("-" * 88)
                for kb in kbs:
                    name = kb.get("kb_name", "未命名")[:26]
                    b_type = kb.get("base_type", "知识库")
                    count = kb.get("content_count", "0")
                    kb_id = kb.get("kb_id", "")
                    print(f"{name:<28} | {b_type:<12} | {count:<6} | {kb_id}")

        elif args.command == "get-kb":
            actual_id = client.resolve_kb_id(args.kb_id)
            info = client.get_knowledge_base(actual_id)
            print(json.dumps(info, ensure_ascii=False, indent=2))

        elif args.command == "search":
            actual_id = client.resolve_kb_id(args.kb_id)
            items = client.search_knowledge(actual_id, query=args.query, limit=args.limit)
            if args.format == "json":
                print(json.dumps(items, ensure_ascii=False, indent=2))
            else:
                print(f"🔍 知识库内找到 {len(items)} 条匹配结果：\n")
                print(f"{'标题':<36} | {'类型':<6} | {'media_id'}")
                print("-" * 88)
                for item in items:
                    title = item.get("title", "未命名")[:34]
                    m_type = str(item.get("media_type", "-"))
                    m_id = item.get("media_id", "")
                    print(f"{title:<36} | {m_type:<6} | {m_id}")

        elif args.command == "read":
            info = client.get_media_info(args.media_id)
            if args.format == "json":
                print(json.dumps(info, ensure_ascii=False, indent=2))
            else:
                url_info = info.get("url_info") or {}
                url = url_info.get("url", "")
                note_content = info.get("note_content")
                if note_content:
                    print("📝 笔记正文内容：\n")
                    print(note_content)
                elif url:
                    print(f"🔗 原文下载/访问直链（带签名）：\n{url}")
                    if info.get("media_type") in (7, 13):
                        try:
                            headers = url_info.get("headers") or {}
                            text_resp = requests.get(url, headers=headers, timeout=15)
                            if text_resp.status_code == 200:
                                print("\n📄 文档正文内容预览：\n")
                                print("-" * 60)
                                print(text_resp.text)
                        except Exception:
                            pass
                else:
                    print(json.dumps(info, ensure_ascii=False, indent=2))

        elif args.command == "read-note":
            doc = client.get_note_content(args.note_id)
            if args.format == "json":
                print(json.dumps(doc, ensure_ascii=False, indent=2))
            else:
                print(doc.get("content", ""))

        elif args.command == "create-note":
            content_text = args.content
            # 如果传入的是本地已有文件路径，自动读取
            if Path(content_text).is_file():
                content_text = Path(content_text).read_text(encoding="utf-8")
            res = client.create_note(args.title, content_text, folder_name=args.folder)
            if args.format == "json":
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                doc_id = res.get("doc_id") or res.get("id")
                print(f"✅ 笔记创建成功！doc_id: {doc_id}")

        elif args.command == "add-note":
            res = client.add_note_to_knowledge_base(args.kb_id, args.note_id, args.title)
            print("✅ 笔记已成功收录至知识库！")
            if args.format == "json":
                print(json.dumps(res, ensure_ascii=False, indent=2))

        elif args.command == "import-urls":
            res = client.import_urls(args.kb_id, args.urls)
            print(f"✅ 已成功提交导入 {len(args.urls)} 个网页 URL！")
            if args.format == "json":
                print(json.dumps(res, ensure_ascii=False, indent=2))

        elif args.command == "upload":
            res = client.upload_file(args.kb_id, args.file_path, folder_id=args.folder_id)
            print(f"✅ {res['message']}")
            print(f"   - 媒体 ID: {res['media_id']}")

        elif args.command == "check-names":
            res = client.check_repeated_names(args.kb_id, args.files)
            print(json.dumps(res, ensure_ascii=False, indent=2))

        elif args.command == "list-addable":
            res = client.get_addable_knowledge_base_list()
            print(json.dumps(res, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"❌ 执行失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
