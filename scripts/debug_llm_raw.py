"""直接调 LLM 看它实际返回什么(不经后处理)"""
import os, sys, time, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from api._llm import call_llm, load_prompt

# 用真实 B 站用户数据测试
profile = {
    "uid": "546195",
    "name": "老番茄",
    "sign": "复旦大学在读,B站百大UP主",
    "level": 6,
    "fans": 20548979,
    "following": 5,
    "vipType": 2,
    "vipLabel": "年度大会员",
    "official": {"role": 1, "title": "2025百大UP主"},
    "regtime": 1451577600,
    "joinDays": 3600,
    "videos": [
        {"title": "我做了一款B站游戏", "length": "15:21", "play": 18000000, "created": 1750000000},
    ],
}
template = load_prompt("user.md")
user = (template
    .replace("{uid}", str(profile["uid"]))
    .replace("{name}", str(profile["name"]))
    .replace("{face}", "")
    .replace("{sex}", "男")
    .replace("{sign}", profile["sign"])
    .replace("{level}", str(profile["level"]))
    .replace("{fans}", str(profile["fans"]))
    .replace("{following}", str(profile["following"]))
    .replace("{vipType}", str(profile["vipType"]))
    .replace("{vipLabel}", profile["vipLabel"])
    .replace("{official_json}", json.dumps(profile["official"], ensure_ascii=False))
    .replace("{regtime}", str(profile["regtime"]))
    .replace("{joinDays}", str(profile["joinDays"]))
    .replace("{videos_json}", json.dumps(profile["videos"], ensure_ascii=False))
)

system = load_prompt("system.md")
print("system prompt length:", len(system))
print("user prompt length:", len(user))
print()
print("=" * 60)
print("调 LLM...")
print("=" * 60)
t0 = time.time()
try:
    result = call_llm(system, user, temperature=0.5, max_tokens=2000)
    print(f"耗时 {(time.time()-t0)*1000:.0f}ms")
    print("返回 keys:", list(result.keys()))
    for k in ("personaType", "pastLife", "craziness"):
        v = result.get(k, "<缺失>")
        if isinstance(v, dict):
            print(f"\n[{k}] type={v.get('type') or v.get('identity') or v.get('level')}")
        else:
            print(f"\n[{k}] 缺失或非 dict: {v!r}")
except Exception as e:
    print(f"!! 失败: {e}")
