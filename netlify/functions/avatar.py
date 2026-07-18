"""
netlify/functions/avatar.py
GET /api/avatar?url=<encoded_bilibili_avatar_url>

头像代理:绕过 Chrome ORB (Opaque Response Blocking)
B 站图片服务器不返回 CORS 头,html2canvas 截屏时会失败。
这里用我们自己的 origin 转发图片字节,加 CORS 头。

SSRF 防护:只允许 hdslb.com / hdslb.cn / bilivideo.com 域名。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64
import logging
from urllib.parse import urlparse

import requests

_ALLOWED_AVATAR_HOSTS = (
    "i0.hdslb.com",
    "i1.hdslb.com",
    "i2.hdslb.com",
    "i0.hdslb.cn",
    "i1.hdslb.cn",
    "i2.hdslb.cn",
    "s1.hdslb.com",
    "s2.hdslb.com",
    "bilivideo.com",
    "bilivideo.cn",
)

logger = logging.getLogger(__name__)


def _is_allowed_avatar_url(url: str) -> bool:
    """严格校验 hostname,防止 SSRF。"""
    if not url or not url.startswith(("http://", "https://")):
        return False
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if not host:
            return False
        return any(host == h or host.endswith("." + h) for h in _ALLOWED_AVATAR_HOSTS)
    except Exception:
        return False


def handler(event, context):
    url = (event.get("queryStringParameters") or {}).get("url", "")
    url = (url or "").strip()
    if not _is_allowed_avatar_url(url):
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "text/plain"},
            "body": "invalid url",
        }

    try:
        r = requests.get(
            url,
            timeout=8,
            stream=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.bilibili.com/",
            },
        )
        r.raise_for_status()
        content_type = r.headers.get("Content-Type", "image/jpeg")
        if not content_type.startswith("image/"):
            r.close()
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "text/plain"},
                "body": "invalid content type",
            }

        downloaded = 0
        chunks = []
        for chunk in r.iter_content(8192):
            downloaded += len(chunk)
            if downloaded > 2 * 1024 * 1024:
                r.close()
                return {
                    "statusCode": 413,
                    "headers": {"Content-Type": "text/plain"},
                    "body": "file too large",
                }
            chunks.append(chunk)
        content = b"".join(chunks)

        # Netlify Functions 用 isBase64Encoded 返回二进制
        b64 = base64.b64encode(content).decode("ascii")
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": content_type,
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=86400",
            },
            "body": b64,
            "isBase64Encoded": True,
        }
    except Exception as exc:
        logger.warning("avatar proxy error url=%s exc=%s", url, exc)
        return {
            "statusCode": 502,
            "headers": {"Content-Type": "text/plain"},
            "body": "proxy error",
        }
