import os, sys
# 统一环境变量名:STEPFUN_API_KEY(兼容 STEP_API_KEY / STEPFUN_TOKEN / AGNES_API_KEY 等历史名)
ks = [k for k in os.environ if 'STEPFUN' in k.upper() or 'STEP_API' in k.upper() or 'AGNES' in k.upper()]
print("API key env vars:", ks)
print("STEPFUN_API_KEY exists:", bool(os.environ.get('STEPFUN_API_KEY')))
print("STEP_API_KEY exists:", bool(os.environ.get('STEP_API_KEY')))
print("STEPFUN_TOKEN exists:", bool(os.environ.get('STEPFUN_TOKEN')))
print("(legacy) AGNES_API_KEY exists:", bool(os.environ.get('AGNES_API_KEY')))
