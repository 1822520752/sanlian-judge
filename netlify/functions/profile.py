"""
netlify/functions/profile.py - Netlify Function: /api/profile

自包含适配器: 将 Netlify event 转给 Vercel 风格 handler。
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

# 将项目根目录加入 sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.profile import handler as vercel_handler


class _Req:
    """把 Netlify event 包装成 Vercel handler 能识别的形态。"""
    def __init__(self, event: Dict[str, Any]):
        self._event = event
    @property
    def query(self) -> Dict[str, str]:
        qs = self._event.get("queryStringParameters") or {}
        return {k: str(v) for k, v in qs.items() if v is not None}
    @property
    def queryStringParameters(self) -> Dict[str, str]:
        return self.query
    @property
    def body(self) -> Dict[str, Any]:
        raw = self._event.get("body") or "{}"
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {}
        return raw if isinstance(raw, dict) else {}
    def get(self, key: str, default: Any = None) -> Any:
        return self._event.get(key, default)


def handler(event, context):
    try:
        result = vercel_handler(_Req(event))
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-store, max-age=0",
            },
            "body": json.dumps(result, ensure_ascii=False),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"code": -1, "data": None, "error": str(e)}, ensure_ascii=False),
        }