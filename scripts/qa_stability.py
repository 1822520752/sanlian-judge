"""多账号稳定性测试"""
import sys, time
sys.path.insert(0, '.')
from api.analyze import handler
from api.profile import handler as ph

for uid in ('546195', '10086', '1'):
    t0 = time.time()
    p = ph({'query': {'uid': uid}})
    if p.get('code') != 0:
        err = p.get('error', '?')
        print(f'UID {uid}: profile FAIL: {err[:150]}')
        continue
    name = p['data'].get('name')
    r = handler({'body': {'uid': uid, 'profile': p['data']}})
    el = (time.time()-t0)*1000
    if r.get('code') != 0:
        err = r.get('error', '?')
        print(f'UID {uid} ({name}): FAIL {el:.0f}ms: {err[:200]}')
        continue
    d = r['data']
    cr = d.get('craziness', {}).get('score', '?')
    pt = d.get('personaType', {}).get('type', '?')[:30]
    keys = [k for k in ('personaType','pastLife','mentalState','fortune2026','soulMate','danmuStyle','craziness') if d.get(k)]
    print(f'UID {uid} ({name}): OK {el:.0f}ms | 离谱={cr}% | 人格={pt} | 模块 {len(keys)}/7')
