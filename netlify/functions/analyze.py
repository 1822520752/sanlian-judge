"""
netlify/functions/analyze.py
POST /api/analyze

Body: {uid, profile?}
直接调用 api/analyze.py handler,无需业务代码改动。
"""
from netlify.functions._adapter import netlify_handler
from api.analyze import handler as analyze_handler

def handler(event, context):
    return netlify_handler(analyze_handler)(event, context)
