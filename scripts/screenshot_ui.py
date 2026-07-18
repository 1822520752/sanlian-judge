"""
sanlian-judge UI 视觉验证 - Playwright 截图
"""
from playwright.sync_api import sync_playwright
import time
import os

OUT_DIR = r"e:\开发项目文件夹\AI创造公开赛 - 副本\sanlian-judge\ui_screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

# 模拟数据(用于报告页)
MOCK_PROFILE = {
    "uid": "546195",
    "name": "老番茄",
    "face": "https://i2.hdslb.com/bfs/face/9f8e3f5cf1c1a3f5e8e3f5cf1c1a3f5e9f8e3f5c.jpg",
    "sex": "男",
    "sign": "生活就像一盒巧克力",
    "level": 6,
    "fans": 20548979,
    "following": 5,
    "vipType": 2,
    "vipLabel": "年度大会员",
    "official": {"title": "2025百大UP主"},
    "regtime": 1450000000,
    "joinDays": 2912,
}

MOCK_REPORT = {
    "personaType": {
        "type": "毒舌段子手",
        "emoji": "🎭",
        "description": "你用幽默解构一切严肃,弹幕区就是你的脱口秀现场",
        "color": "#ff2d7e",
        "tags": ["输出机器", "热梗王", "赛博rapper"],
        "dimensions": {"毒舌指数": 88, "创作热度": 95, "鸽子概率": 23, "氪金程度": 45},
    },
    "pastLife": {
        "identity": "古罗马剧场里的即兴喜剧演员",
        "era": "公元前 1 世纪",
        "description": "你的灵魂来自古罗马的喜剧舞台,擅长用嬉笑怒骂解构权威,在元老院里讲单口相声,让凯撒都忍不住笑出猪叫。",
        "icon": "🎭",
    },
    "mentalState": {
        "level": "微癫",
        "position": 65,
        "description": "日常稳定但偶尔出戏,容易在深夜刷到某个梗时突然狂笑",
        "mentalAge": "13岁(生理) / 25岁(嘴)",
        "advice": "少熬夜,多出门晒太阳,不要半夜三点和人对线",
    },
    "fortune2026": {
        "career": "创意井喷,会有意外爆款",
        "wealth": "小金库充实,记得理财",
        "love": "暗流涌动,主动一点",
        "abstract": "灵感爆棚期,适合整活",
        "luckyColor": "#ff2d7e",
        "luckyNumber": 7,
    },
    "soulMate": {
        "name": "何同学",
        "mid": "46143887",
        "similarity": 87,
        "reason": "你们都擅长用技术解构生活,在沉默中突然来一句神吐槽",
    },
    "danmuStyle": {
        "oftenSay": ["绷不住了", "破防了", "下次一定", "典中典"],
        "neverSay": ["家人们", "绝绝子", "yyds", "宝藏男孩"],
        "verdict": "你的弹幕风格属于「冷面吐槽」流派,看似随意实则字字珠玑",
        "grade": "S",
    },
    "craziness": {
        "score": 78,
        "ranking": "前 4.2%",
        "verdict": "你的精神世界已超越99%的用户,建议保持现有生活节奏,慎用催产素",
        "level": "非常离谱",
    },
}

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ========== 1. 移动端首页(375x812, iPhone 13 尺寸) ==========
        ctx = browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2)
        page = ctx.new_page()
        page.goto("http://localhost:8000/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(1)  # 等待字体加载
        page.screenshot(path=os.path.join(OUT_DIR, "01_home_mobile.png"))
        print("OK: 01_home_mobile.png")

        # 截图全页
        page.screenshot(path=os.path.join(OUT_DIR, "01_home_mobile_full.png"), full_page=True)
        print("OK: 01_home_mobile_full.png")

        # ========== 2. 输入 UID 后 ==========
        page.fill("#uid-input", "546195")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(OUT_DIR, "02_home_filled.png"))
        print("OK: 02_home_filled.png")

        # ========== 3. 注入 mock 数据,直接渲染报告页 ==========
        page.evaluate("""
            (() => {
                const profile = %s;
                const report = %s;
                const uid = '546195';
                if (window.CyberJudgeReport && window.CyberJudgeReport.render) {
                    window.CyberJudgeReport.render(profile, report, uid, false);
                }
                // 切到报告页
                if (window.CyberJudge && window.CyberJudge.showPage) {
                    window.CyberJudge.showPage('report');
                }
                // 强制让所有模块可见
                document.querySelectorAll('.module').forEach(m => m.classList.add('in-view'));
            })();
        """ % (
            str(MOCK_PROFILE).replace("'", '"').replace("True", "true").replace("False", "false"),
            str(MOCK_REPORT).replace("'", '"'),
        ))
        time.sleep(0.5)
        page.screenshot(path=os.path.join(OUT_DIR, "03_report_top.png"))
        print("OK: 03_report_top.png")

        # 报告页全屏滚动截图
        page.screenshot(path=os.path.join(OUT_DIR, "04_report_full.png"), full_page=True)
        print("OK: 04_report_full.png")

        # ========== 4. 桌面端 1280x800 首页 ==========
        ctx2 = browser.new_context(viewport={"width": 1280, "height": 800})
        page2 = ctx2.new_page()
        page2.goto("http://localhost:8000/index.html")
        page2.wait_for_load_state("networkidle")
        time.sleep(1)
        page2.screenshot(path=os.path.join(OUT_DIR, "05_home_desktop.png"))
        print("OK: 05_home_desktop.png")

        # 桌面端报告页
        page2.evaluate("""
            (() => {
                const profile = %s;
                const report = %s;
                if (window.CyberJudgeReport && window.CyberJudgeReport.render) {
                    window.CyberJudgeReport.render(profile, report, '546195', false);
                }
                if (window.CyberJudge && window.CyberJudge.showPage) {
                    window.CyberJudge.showPage('report');
                }
                document.querySelectorAll('.module').forEach(m => m.classList.add('in-view'));
            })();
        """ % (
            str(MOCK_PROFILE).replace("'", '"'),
            str(MOCK_REPORT).replace("'", '"'),
        ))
        time.sleep(0.5)
        page2.screenshot(path=os.path.join(OUT_DIR, "06_report_desktop.png"))
        print("OK: 06_report_desktop.png")

        browser.close()
        print("\n所有截图保存到: %s" % OUT_DIR)

if __name__ == "__main__":
    main()
