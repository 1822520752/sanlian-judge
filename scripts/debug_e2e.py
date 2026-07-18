"""直接 hit /api/analyze 看后端返回"""
import json, time, urllib.request, urllib.error

body = json.dumps({
    "uid": "546195",
    "profile": {
        "uid": "546195",
        "name": "老番茄",
        "face": "https://example.com/face.png",
        "sex": "男",
        "sign": "复旦大学在读,B站百大UP主,游戏区扛把子",
        "level": 6,
        "fans": 20548979,
        "following": 5,
        "vipType": 2,
        "vipLabel": "年度大会员",
        "official": {"role": 1, "title": "2025百大UP主", "desc": "知名UP主"},
        "regtime": 1451577600,
        "joinDays": 3600,
        "videos": [
            {"title": "我做了一款B站游戏", "length": "15:21", "play": 18000000, "created": 1750000000},
            {"title": "实况解说:生化危机", "length": "23:45", "play": 12000000, "created": 1749000000},
        ],
    }
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:5000/api/analyze",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
t0 = time.time()
try:
    r = urllib.request.urlopen(req, timeout=180)
    print(f"耗时 {(time.time()-t0)*1000:.0f}ms, status {r.status}")
    print(r.read().decode("utf-8")[:1500])
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode('utf-8')[:800]}")
except Exception as e:
    print(f"Error: {e}")
