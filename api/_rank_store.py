"""
api/_rank_store.py - 排行榜读写存储

策略:
  1) 优先使用 Vercel KV(环境变量 KV_REST_API_URL + KV_REST_API_TOKEN)
  2) 降级使用本地文件 data/rank.json(文件兜底,Vercel Serverless 中只读根目录)

读写接口:
  - write_rank(item)         写入一条记录(KV 或文件)
  - read_rank(page, limit)   读取并按 score 降序分页返回

榜单 item 字段:
  {
    "uid": str,
    "name": str,
    "score": int,
    "level": str,
    "avatar": str,
    "timestamp": int   # Unix 秒
  }
"""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

# 排行榜最多保留多少条(可通过环境变量调整)
MAX_RANK_ENTRIES = int(os.environ.get("MAX_RANK_ENTRIES", "50"))
DEFAULT_DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "rank.json",
)
KV_KEY = "cyber-judge:rank:list"

# 全局锁:序列化 write_rank,防止并发读-改-写丢数据(dev_server 单进程足够)
_rank_write_lock = threading.Lock()


def _safe_score(item: Dict[str, Any]) -> int:
    """安全提取 score,非数字返回 0。"""
    try:
        return int(item.get("score", 0) or 0)
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# KV 读写
# ---------------------------------------------------------------------------


def _kv_request(method: str, url_suffix: str) -> Optional[Any]:
    """向 Vercel KV REST API 发起请求,失败返回 None。"""
    base = os.environ.get("KV_REST_API_URL")
    token = os.environ.get("KV_REST_API_TOKEN")
    if not base or not token:
        return None
    try:
        import requests  # 局部 import 避免无 KV 时引入开销

        url = base.rstrip("/") + url_suffix
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.request(method, url, headers=headers, timeout=2)
        if resp.status_code >= 400:
            return None
        return resp.json()
    except Exception:
        return None


def _kv_read_list() -> Optional[List[Dict[str, Any]]]:
    data = _kv_request("GET", f"/get/{KV_KEY}")
    if data is None:
        return None
    # Vercel KV REST 响应: {"result": "<json-string>"}
    raw = data.get("result") if isinstance(data, dict) else None
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        return []
    return []


def _kv_write_list(items: List[Dict[str, Any]]) -> bool:
    base = os.environ.get("KV_REST_API_URL")
    token = os.environ.get("KV_REST_API_TOKEN")
    if not base or not token:
        return False
    try:
        import requests

        url = base.rstrip("/") + f"/set/{KV_KEY}"
        headers = {"Authorization": f"Bearer {token}"}
        # 注意:必须用 json.dumps 后作为 raw body 传
        # 加 EX 30 天 TTL,避免 KV 容量无限增长
        resp = requests.request(
            "POST",
            url,
            headers=headers,
            json=[json.dumps(items, ensure_ascii=False), "EX", 2592000],
            timeout=2,
        )
        return resp.status_code < 400
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 文件兜底读写
# ---------------------------------------------------------------------------


def _ensure_data_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)


def _file_read_list(path: str) -> List[Dict[str, Any]]:
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        # 文件损坏,备份后返回空,避免后续写入覆盖原数据
        try:
            shutil.copy(path, path + f".corrupt.{int(time.time())}")
        except Exception:
            pass
        return []
    except Exception:
        return []
    return []


def _file_write_list(path: str, items: List[Dict[str, Any]]) -> bool:
    """原子写入:先写临时文件,再 os.replace 替换(防止崩溃留半截 JSON)。"""
    try:
        _ensure_data_dir(path)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)  # 原子替换
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------


def _merge_and_trim(
    existing: List[Dict[str, Any]], new_item: Dict[str, Any], limit: int = MAX_RANK_ENTRIES
) -> List[Dict[str, Any]]:
    """按 uid 去重,加入 new_item 后按 score 降序裁剪到 limit。"""
    uid = str(new_item.get("uid", "")).strip()
    if not uid:
        return existing
    merged = [it for it in existing if str(it.get("uid", "")) != uid]
    merged.append(new_item)
    merged.sort(key=_safe_score, reverse=True)
    return merged[:limit]


def write_rank(item: Dict[str, Any]) -> bool:
    """
    写入一条排行榜记录,优先 KV,失败则写文件。
    加全局锁序列化,防止并发读-改-写丢数据。

    item = {uid, name, score, level, avatar, timestamp}
    返回是否写入成功(KV 或文件任一成功即视为成功)。
    """
    if not item.get("uid"):
        return False
    item.setdefault("timestamp", int(time.time()))

    with _rank_write_lock:
        # 1) KV 优先
        existing = _kv_read_list()
        if existing is not None:
            merged = _merge_and_trim(existing, item)
            if _kv_write_list(merged):
                return True

        # 2) 文件兜底
        items = _file_read_list(DEFAULT_DATA_FILE)
        merged = _merge_and_trim(items, item)
        return _file_write_list(DEFAULT_DATA_FILE, merged)


def read_rank(
    page: int = 1, limit: int = 20, rank_type: str = "craziness"
) -> Tuple[List[Dict[str, Any]], int]:
    """
    读取排行榜,按 score 降序,返回 (list, total)。

    rank_type 当前仅支持 craziness,保留字段便于以后扩展。
    """
    items: Optional[List[Dict[str, Any]]] = _kv_read_list()
    if items is None:
        items = _file_read_list(DEFAULT_DATA_FILE)

    # 过滤非法条目
    cleaned: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        if "uid" not in it or "score" not in it:
            continue
        cleaned.append(it)

    cleaned.sort(key=_safe_score, reverse=True)
    total = len(cleaned)

    # 分页
    try:
        page = max(1, int(page))
        limit = max(1, min(100, int(limit)))
    except Exception:
        page, limit = 1, 20

    start = (page - 1) * limit
    end = start + limit
    return cleaned[start:end], total
