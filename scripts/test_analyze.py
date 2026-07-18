"""
scripts/test_analyze.py - 本地调试 LLM Prompt 模板 (Agnes AI)

用法:
    # 1) 默认 mock profile,直接验证 Prompt + Agnes 调用
    python scripts/test_analyze.py

    # 2) 指定一个真实 UID,先拉 profile 再分析
    python scripts/test_analyze.py 546195

说明:
    - 需要环境变量 AGNES_API_KEY 已设置(或 AGNES_API_TOKEN / APIHUB_AGNES_API_KEY)
    - 不会写入排行榜(那是 /api/analyze 的事),纯打印
"""

from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api._llm import call_llm, load_prompt  # noqa: E402
from api.profile import handler as profile_handler  # noqa: E402


MOCK_PROFILE = {
    "uid": "99999999",
    "name": "测试UP主",
    "face": "https://example.com/face.png",
    "sex": "保密",
    "sign": "这是一个用于测试的签名",
    "level": 5,
    "fans": 12345,
    "following": 200,
    "vipType": 0,
    "vipLabel": None,
    "official": {"role": 0, "title": "", "desc": ""},
    "regtime": 1500000000,
    "joinDays": 3000,
    "videos": [
        {"title": "测试视频标题 A", "length": "03:21", "play": 9999, "created": 1700000000}
    ],
}


def build_user_prompt(profile: dict) -> str:
    template = load_prompt("user.md")
    return (
        template
        .replace("{uid}", str(profile.get("uid", "")))
        .replace("{name}", str(profile.get("name", "")))
        .replace("{face}", str(profile.get("face", "")))
        .replace("{sex}", str(profile.get("sex", "")))
        .replace("{sign}", str(profile.get("sign", "")))
        .replace("{level}", str(profile.get("level", 0)))
        .replace("{fans}", str(profile.get("fans", 0)))
        .replace("{following}", str(profile.get("following", 0)))
        .replace("{vipType}", str(profile.get("vipType", 0)))
        .replace("{vipLabel}", str(profile.get("vipLabel") or ""))
        .replace("{official_json}", json.dumps(profile.get("official", {}), ensure_ascii=False))
        .replace("{regtime}", str(profile.get("regtime", 0)))
        .replace("{joinDays}", str(profile.get("joinDays", 0)))
        .replace("{videos_json}", json.dumps(profile.get("videos", []), ensure_ascii=False))
    )


def get_profile(uid: str) -> dict:
    result = profile_handler({"query": {"uid": uid}})
    if result.get("code") != 0:
        print(f"!! profile 拉取失败: {result.get('error')}")
        return MOCK_PROFILE
    return result["data"]


def main() -> int:
    if not (os.environ.get("AGNES_API_KEY") or os.environ.get("AGNES_API_TOKEN") or os.environ.get("APIHUB_AGNES_API_KEY")):
        print("!! 缺少 AGNES_API_KEY 环境变量,无法调用 LLM")
        return 1

    if len(sys.argv) > 1:
        uid = sys.argv[1]
        profile = get_profile(uid)
    else:
        profile = MOCK_PROFILE

    print("\n=== 输入 profile ===")
    print(json.dumps(profile, ensure_ascii=False, indent=2))

    system_prompt = load_prompt("system.md")
    user_prompt = build_user_prompt(profile)

    print("\n=== 调用 Agnes ... ===")
    t0 = time.time()
    result = call_llm(system_prompt, user_prompt)
    print(f"耗时: {(time.time() - t0) * 1000:.0f}ms")

    print("\n=== 返回 JSON ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 模块完整性检查
    required = [
        "personaType", "pastLife", "mentalState",
        "fortune2026", "soulMate", "danmuStyle", "craziness",
    ]
    missing = [k for k in result if k not in required and k not in []]
    missing = [k for k in required if k not in result]
    if missing:
        print(f"\n!! 警告: 缺少模块 {missing}")
        return 2
    print("\n=== 7 个模块齐全,Prompt 模板与 Agnes 调用验证通过 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
