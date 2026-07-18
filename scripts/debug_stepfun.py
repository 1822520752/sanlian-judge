"""最小测试:StepFun API 是否接得通"""
import os, json, requests, time

key = os.environ['STEPFUN_API_KEY']
url = "https://api.stepfun.com/step_plan/v1/chat/completions"

# 候选模型
candidates = ["step-1-8k", "step-1", "step-1-32k", "step-2-mini", "step-1-128k"]
payload = {
    "model": None,  # 占位
    "messages": [
        {"role": "system", "content": "你是 JSON 生成器。"},
        {"role": "user", "content": '输出这个 JSON:{"ok":true}。只输出 JSON。'},
    ],
    "temperature": 0.1,
    "max_tokens": 200,
    "response_format": {"type": "json_object"},
}

headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

for m in candidates:
    payload["model"] = m
    t0 = time.time()
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        elapsed = (time.time()-t0)*1000
        print(f"\n=== model={m} | {r.status_code} | {elapsed:.0f}ms ===")
        if r.status_code == 200:
            d = r.json()
            msg = d['choices'][0]['message']
            print("content:", repr(msg.get('content','')[:200]))
            print("usage:  ", d.get('usage'))
        else:
            print("body:", r.text[:300])
    except Exception as e:
        print(f"  !! exception: {e}")
