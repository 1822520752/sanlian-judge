"""直接调 B 站接口看错误"""
import sys, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from api.profile import get_profile, handler

# 测试 3 个不同类型 UID
for uid in ["546195", "10086", "1"]:
    print("=" * 60)
    print(f"UID: {uid}")
    print("=" * 60)
    r = handler({"query": {"uid": uid}})
    print(f"code: {r['code']}, error: {r.get('error')}")
    if r["code"] == 0:
        d = r["data"]
        print(f"  name: {d.get('name')}")
        print(f"  face: {d.get('face')}")
        print(f"  fans: {d.get('fans')}")
        print(f"  videos: {len(d.get('videos', []))}")
    print()
