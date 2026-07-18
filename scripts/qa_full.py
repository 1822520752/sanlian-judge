"""完整端到端测试"""
import os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.analyze import handler as analyze_handler

cases = [
    {"name": "老番茄(大号)", "uid": "546195"},
    {"name": "1粉新人", "profile": {
        "uid": "1", "name": "测试", "face": "", "sex": "保密", "sign": "",
        "level": 0, "fans": 0, "following": 0, "vipType": 0, "vipLabel": "",
        "official": {"role": 0, "title": "", "desc": ""},
        "regtime": 0, "joinDays": 0, "videos": []
    }},
]

for c in cases:
    print("=" * 60)
    print(f"案例: {c['name']}")
    print("=" * 60)
    if "uid" in c and "profile" not in c:
        # uid only - 自行拉
        req = {"body": {"uid": c["uid"], "profile": None}}
    else:
        req = {"body": c}
    t0 = time.time()
    r = analyze_handler(req)
    elapsed = (time.time()-t0)*1000
    print(f"  {elapsed:.0f}ms, code={r.get('code')}")
    if r.get("code") != 0:
        print(f"  !! error: {r.get('error')}")
        continue
    data = r["data"]
    # 检查 7 模块齐全
    for k in ("personaType", "pastLife", "mentalState", "fortune2026", "soulMate", "danmuStyle", "craziness"):
        v = data.get(k)
        if v is None:
            print(f"  !! 缺失模块: {k}")
        else:
            t = type(v).__name__
            keys = list(v.keys()) if hasattr(v, "keys") else []
            print(f"  ✓ {k} ({t}) keys={keys[:5]}")
    # 字段检查
    pt = data.get("personaType", {})
    if pt.get("type") == "B站普通用户":
        print("  !! 警告: personaType 用了默认 'B站普通用户'")
    cr = data.get("craziness", {})
    if cr.get("score") == 50:
        print("  !! 警告: craziness.score 用了默认 50")
    print()
