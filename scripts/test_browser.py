#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""浏览器 UI 测试 - 使用 Playwright 验证前端功能和分享卡生成"""
import os
import sys
import time
import json
from pathlib import Path

# 截图保存目录
SHOT_DIR = Path(r"e:\开发项目文件夹\AI创造公开赛 - 副本\sanlian-judge\test_screenshots")
SHOT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    from playwright.sync_api import sync_playwright

    results = {"pass": 0, "fail": 0, "warn": 0}

    def log(ok, msg):
        key = "pass" if "PASS" in ok else ("fail" if "FAIL" in ok else "warn")
        results[key] += 1
        print(f"  {ok} {msg}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            locale="zh-CN",
        )
        page = context.new_page()

        # 收集 console 错误
        console_errors = []
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda err: console_errors.append(f"[pageerror] {err}"))

        print("\n" + "=" * 60)
        print(" [1] 首页加载测试")
        print("=" * 60)

        try:
            page.goto("http://localhost:5000", wait_until="networkidle", timeout=30000)
            title = page.title()
            if "sanlian-judge" in title:
                log("✓ PASS", f"首页标题: {title}")
            else:
                log("✗ FAIL", f"首页标题异常: {title}")

            # 截图
            page.screenshot(path=str(SHOT_DIR / "01_home.png"), full_page=False)
            log("✓ PASS", "首页截图已保存")

            # 检查关键元素
            if page.locator("#uid-input").is_visible():
                log("✓ PASS", "UID 输入框可见")
            else:
                log("✗ FAIL", "UID 输入框不可见")

            if page.locator("#btn-submit").is_visible():
                log("✓ PASS", "执行判决按钮可见")
            else:
                log("✗ FAIL", "执行判决按钮不可见")

            # 检查示例 UID
            examples = page.locator(".example-uid").count()
            if examples >= 3:
                log("✓ PASS", f"示例 UID 按钮数量: {examples}")
            else:
                log("⚠ WARN", f"示例 UID 按钮数量: {examples}")

        except Exception as e:
            log("✗ FAIL", f"首页加载异常: {e}")

        print("\n" + "=" * 60)
        print(" [2] 输入 UID 并分析(老番茄 546195)")
        print("=" * 60)

        try:
            page.fill("#uid-input", "546195")
            log("✓ PASS", "UID 输入成功")

            # 点击执行判决
            page.click("#btn-submit")
            log("✓ PASS", "点击执行判决按钮")

            # 等待 loading 页出现
            page.wait_for_selector("#page-loading:not(.hidden)", timeout=5000)
            log("✓ PASS", "Loading 页显示")
            page.screenshot(path=str(SHOT_DIR / "02_loading.png"), full_page=False)

            # 等待报告页(最多 3 分钟)
            print("  等待 AI 分析完成(最多 3 分钟)...")
            try:
                page.wait_for_selector("#page-report:not(.hidden)", timeout=180000)
                log("✓ PASS", "报告页显示")
            except Exception:
                log("✗ FAIL", "报告页 3 分钟内未显示")
                page.screenshot(path=str(SHOT_DIR / "02_loading_timeout.png"), full_page=False)
                browser.close()
                print_summary(results, console_errors)
                return

            # 等待渲染
            time.sleep(2)
            page.screenshot(path=str(SHOT_DIR / "03_report_top.png"), full_page=False)
            log("✓ PASS", "报告页截图已保存(顶部)")

            # 检查报告模块
            modules = page.locator(".module").count()
            if modules >= 7:
                log("✓ PASS", f"报告模块数量: {modules}")
            else:
                log("⚠ WARN", f"报告模块数量: {modules}(期望 7-8)")

            # 滚动截图
            page.screenshot(path=str(SHOT_DIR / "04_report_full.png"), full_page=True)
            log("✓ PASS", "报告页完整截图已保存")

        except Exception as e:
            log("✗ FAIL", f"分析流程异常: {e}")
            page.screenshot(path=str(SHOT_DIR / "error_analysis.png"), full_page=False)

        print("\n" + "=" * 60)
        print(" [3] 分享卡生成测试")
        print("=" * 60)

        try:
            # 点击 SHARE 按钮
            share_btn = page.locator("#btn-share")
            if share_btn.is_visible():
                share_btn.click()
                log("✓ PASS", "点击 SHARE 按钮")

                # 等待下载或 toast
                time.sleep(5)
                page.screenshot(path=str(SHOT_DIR / "05_after_share.png"), full_page=False)

                # 检查是否有 toast 提示
                toast = page.locator(".toast").count()
                if toast > 0:
                    toast_text = page.locator(".toast").first.inner_text()
                    log("✓ PASS", f"Toast 提示: {toast_text[:50]}")
                else:
                    log("⚠ WARN", "未看到 toast 提示")

                # 检查 share-target 是否有内容
                share_target = page.locator("#share-target")
                if share_target:
                    html = share_target.inner_html()
                    if html and len(html) > 100:
                        log("✓ PASS", f"分享卡 HTML 已生成({len(html)} 字符)")
                    else:
                        log("⚠ WARN", f"分享卡 HTML 内容较少: {len(html)} 字符")
            else:
                log("✗ FAIL", "SHARE 按钮不可见")

        except Exception as e:
            log("✗ FAIL", f"分享卡生成异常: {e}")

        print("\n" + "=" * 60)
        print(" [4] 排行榜测试")
        print("=" * 60)

        try:
            rank_btn = page.locator("#btn-rank")
            if rank_btn.is_visible():
                rank_btn.click()
                log("✓ PASS", "点击 RANK 按钮")

                time.sleep(2)
                page.screenshot(path=str(SHOT_DIR / "06_rank.png"), full_page=False)

                modal = page.locator("#modal-rank:not(.hidden)")
                if modal.count() > 0:
                    log("✓ PASS", "排行榜弹窗显示")
                    items = page.locator(".rank-item").count()
                    log("✓ PASS" if items > 0 else "⚠ WARN", f"排行榜条目: {items}")
                else:
                    log("⚠ WARN", "排行榜弹窗未显示(可能无数据)")

                # 关闭弹窗
                page.keyboard.press("Escape")
                time.sleep(1)
            else:
                log("⚠ WARN", "RANK 按钮不可见")

        except Exception as e:
            log("✗ FAIL", f"排行榜测试异常: {e}")

        print("\n" + "=" * 60)
        print(" [5] 控制台错误检查")
        print("=" * 60)

        if console_errors:
            for err in console_errors[:10]:
                log("⚠ WARN", f"Console: {err[:100]}")
            if len(console_errors) > 10:
                log("⚠ WARN", f"... 还有 {len(console_errors) - 10} 条错误")
        else:
            log("✓ PASS", "无 console 错误")

        browser.close()

    print_summary(results, console_errors)


def print_summary(results, console_errors):
    print("\n" + "=" * 60)
    print(" 浏览器测试总结")
    print("=" * 60)
    total = results["pass"] + results["fail"] + results["warn"]
    print(f"  通过: {results['pass']}/{total}")
    print(f"  失败: {results['fail']}/{total}")
    print(f"  警告: {results['warn']}/{total}")
    rate = results["pass"] / total * 100 if total else 0
    print(f"  通过率: {rate:.1f}%")
    print(f"  Console 错误: {len(console_errors)} 条")
    print(f"  截图保存: {SHOT_DIR}")
    print("=" * 60)
    sys.exit(0 if results["fail"] == 0 else 1)


if __name__ == "__main__":
    main()
