"""测试极低粉/无数据账号能否正常分析"""
import os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from api.analyze import handler as analyze_handler

# 模拟 3 种"低数据"账号
cases = [
    {
        "name": "0粉新人",
        "uid": "10086",
        "profile": {
            "uid": "10086",
            "name": "路过的咸鱼",
            "face": "https://example.com/face.png",
            "sex": "保密",
            "sign": "随便看看",
            "level": 2,
            "fans": 0,
            "following": 3,
            "vipType": 0,
            "vipLabel": "",
            "official": {"role": 0, "title": "", "desc": ""},
            "regtime": 1730000000,
            "joinDays": 30,
            "videos": [],
        },
    },
    {
        "name": "32粉小透明",
        "uid": "10087",
        "profile": {
            "uid": "10087",
            "name": "深夜潜水员",
            "face": "",
            "sex": "女",
            "sign": "🌙",
            "level": 3,
            "fans": 32,
            "following": 187,
            "vipType": 0,
            "vipLabel": "",
            "official": {"role": 0, "title": "", "desc": ""},
            "regtime": 1715000000,
            "joinDays": 200,
            "videos": [{"title": "随手拍的天空", "length": "00:42", "play": 156, "created": 1740000000}],
        },
    },
    {
        "name": "1.2万粉普通号",
        "uid": "10088",
        "profile": {
            "uid": "10088",
            "name": "小镇做题家",
            "face": "",
            "sex": "男",
            "sign": "理性·克制·偶尔上头",
            "level": 5,
            "fans": 12345,
            "following": 234,
            "vipType": 1,
            "vipLabel": "大会员",
            "official": {"role": 0, "title": "", "desc": ""},
            "regtime": 1600000000,
            "joinDays": 1800,
            "videos": [
                {"title": "我用Excel画了一张猫", "length": "03:21", "play": 8932, "created": 1745000000},
            ],
        },
    },
]

for c in cases:
    print("=" * 60)
    print(f"测试: {c['name']} | UID={c['uid']} | 粉丝={c['profile']['fans']}")
    print("=" * 60)
    t0 = time.time()
    r = analyze_handler({"body": c})
    elapsed = (time.time()-t0)*1000
    print(f"  耗时 {elapsed:.0f}ms, code={r.get('code')}")
    if r.get("code") != 0:
        print(f"  !! error: {r.get('error')}")
        continue
    data = r["data"]
    pt = data.get("personaType", {})
    cr = data.get("craziness", {})
    pl = data.get("pastLife", {})
    print(f"  人格: {pt.get('type')} {pt.get('emoji')}")
    print(f"  描述: {pt.get('description', '')[:80]}...")
    print(f"  离谱: {cr.get('score')}% - {cr.get('level')}")
    print(f"  前世: {pl.get('icon')} {pl.get('identity')} / {pl.get('era')}")
    print(f"  灵魂伴侣: {data.get('soulMate', {}).get('name')} ({data.get('soulMate', {}).get('similarity')}%)")
    print()
