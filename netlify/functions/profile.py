"""
netlify/functions/profile.py
GET /api/profile?uid={uid}

直接调用 api/profile.py handler,无需业务代码改动。
"""
from netlify.functions._adapter import netlify_handler
from api.profile import handler as profile_handler

def handler(event, context):
    return netlify_handler(profile_handler)(event, context)
