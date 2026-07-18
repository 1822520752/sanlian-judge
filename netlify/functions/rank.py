"""
netlify/functions/rank.py
GET /api/rank?type=craziness&page=1&limit=20

直接调用 api/rank.py handler,无需业务代码改动。
"""
from netlify.functions._adapter import netlify_handler
from api.rank import handler as rank_handler

def handler(event, context):
    return netlify_handler(rank_handler)(event, context)
