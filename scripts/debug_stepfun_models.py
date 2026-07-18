"""列出 StepFun 可用模型"""
import os, requests

key = os.environ['STEPFUN_API_KEY']
url = "https://api.stepfun.com/step_plan/v1/models"

r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=15)
print("status:", r.status_code)
print("body:", r.text[:2000])
