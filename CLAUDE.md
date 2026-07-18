# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**三连鉴定委员会 (Sanlian Judge)** — 丢一个B站UID进来，委员会调用 B站 API + StepFun AI 生成一份"半认真半整活"的9模块鉴定证书。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | HTML5 + 自定义 CSS (Neo-Brutalist) + 原生 JS (6 个文件，无框架无构建) |
| 后端 | Python 3.11，Serverless 风格，本地 Flask 开发 |
| B站数据 | `bilibili-api-python` v17.4.2，4 接口并行 (user_info / relation_info / overview_stat / videos) |
| LLM | StepFun (阶跃星辰) `step-3.7-flash`，OpenAI 兼容协议，`response_format=json_object`，单次返回 7 模块 JSON |
| 存储 | Vercel KV 优先，降级为 `data/rank.json` 文件兜底 |
| 部署 | Netlify (主要) / Vercel (兼容) |

## 目录结构

```
.
├── api/                            # 后端业务逻辑 (Vercel/Netlify/Flask 三兼容)
│   ├── profile.py                  # GET /api/profile  B站用户数据
│   ├── analyze.py                  # POST /api/analyze  StepFun AI 鉴定
│   ├── rank.py                     # GET /api/rank     离谱排行榜
│   ├── _llm.py                     # StepFun LLM 调用 + JSON 容错解析 + prompt 加载
│   └── _rank_store.py              # 排行榜 KV/文件双写 (全局锁 + 原子写入)
├── prompts/
│   ├── system.md                   # 系统 Prompt (首席鉴定官口吻 + JSON 硬约束)
│   └── user.md                     # 7 模块合并的 User Prompt 模板 (含占位符)
├── data/
│   └── rank.json                   # 排行榜预置数据 (11 条真实 B 站 UP 主)
├── static/
│   ├── css/
│   │   └── style.css               # B站双品牌色 + Neo-Brutalist 设计系统
│   ├── fonts/
│   │   └── SmileySans-Oblique.*    # 得意黑字体 (4 种格式, woff2 优先)
│   ├── fonts.css                   # @font-face 声明
│   └── js/
│       ├── brand.js                # 主应用入口: UID 输入 → 加载 → 渲染 (全局命名空间 sanlian)
│       ├── report.js               # 鉴定证书 7+2 模块渲染 + 三连按钮 + 弹幕评论流
│       ├── share.js                # html2canvas 分享卡生成 (1080×N PNG)
│       ├── rank.js                 # 排行榜弹窗
│       ├── danmu.js                # 弹幕实时轮播 (预设 30+ 条弹幕池)
│       └── cache.js                # localStorage 缓存 (24h TTL + LRU 10)
├── scripts/                        # 调试 + 验证脚本
│   ├── dev_server.py               # 一体化 Flask 开发服务器 (端口 5000)
│   ├── test_profile.py             # 调试 B站 API
│   ├── test_analyze.py             # 端到端调 LLM
│   ├── verify_mvp.py               # MVP 端到端验证 (11 项检查)
│   ├── qa_full.py                  # 全量 QA 测试
│   ├── qa_stability.py             # 稳定性测试
│   ├── debug_profile.py            # 多 UID profile 调试
│   ├── debug_stepfun.py            # StepFun 模型测试
│   ├── debug_stepfun_models.py     # 列出 StepFun 可用模型
│   ├── debug_e2e.py                # 端到端调试 (profile + analyze)
│   ├── debug_llm_raw.py            # LLM 原始响应诊断
│   ├── test_browser.py             # 浏览器自动化测试
│   ├── test_full.py                # 全流程测试
│   ├── test_low_fans.py            # 边缘情况: 低粉丝用户
│   ├── screenshot_ui.py            # UI 截图
│   └── check_env.py                # 环境检查
├── index.html                      # 单页 SPA 入口 (html2canvas CDN)
├── netlify.toml                    # Netlify 部署配置 (Python 3.11)
├── vercel.json                     # Vercel 部署配置 (兼容)
├── screenshots/                    # UI 截图
├── test_screenshots/               # 测试截图
```

## 9个报告模块

| 模块 | 标题 | 渲染函数 (report.js) | 数据来源 |
|------|------|---------------------|---------|
| 1 | 核心身份卡 | `renderProfile` | B站 API |
| 2 | 弹幕人格类型 | `renderPersona` | LLM |
| 3 | 赛博前世 | `renderPastLife` | LLM |
| 4 | 精神状态评估 | `renderMental` | LLM |
| 5 | 2026运势预测 | `renderFortune` | LLM |
| 6 | 赛博灵魂伴侣 | `renderSoulMate` | LLM |
| 7 | 弹幕风格鉴定 | `renderDanmu` | LLM |
| 8 | 离谱指数 | `renderCraziness` | LLM |
| 9 | 三连按钮 + 弹幕评论流 | (index.html 内联) | 本地 |

模块1直接从 profile 渲染，模块6基于 B站知名UP主池匹配，其余6个模块由 LLM 一次调用生成。

## 关键架构决策

1. **双平台兼容**: 通过 `_FlaskLikeVercelRequest` 适配器类，同一套 `api/*.py` handler 同时支持 Flask (本地)、Vercel、Netlify 三种入口
2. **4 接口并行**: B站数据用 ThreadPoolExecutor(4) 并行调用，串行 ~40s → 并行 ~10s
3. **LLM 单次调用**: 一次 ChatCompletion 输出 7 模块 JSON，成本约 ¥0.01-0.05/次
4. **三级 JSON 容错**: 直接 parse → 找首个平衡 `{...}` 块 → 兜底默认值
5. **排行榜双写**: KV 优先，文件兜底，全局 `_rank_write_lock` 序列化写入
6. **异步排行榜写入**: daemon 线程 + try/catch，写失败不影响主响应
7. **头像代理**: `/api/avatar` 代理 B站 CDN 图片 (SSRF 防护 + 2MB 大小限制 + CORS 头)
8. **前端 无框架 SPA**: 浏览器兼容性手动处理 (WebP/AVIF/JPEG 头像检测)

## 常见开发命令

```bash
# 本地启动 (Flask 开发服务器)
pip install -r requirements.txt
python scripts/dev_server.py
# 访问 http://localhost:5000

# 调试单个 API 脚本 (不需启动服务器)
python scripts/test_profile.py 546195
python scripts/test_analyze.py 546195

# MVP 端到端验证 (检查仓库结构/HTML/JS/Python/Prompt/API 端点)
python scripts/verify_mvp.py

# 全量 QA
python scripts/qa_full.py

# 部署到 Netlify (推送 GitHub → Netlify 自动部署)
# 需设置环境变量 STEPFUN_API_KEY
```

## API 契约

### GET /api/profile?uid={uid}
- 成功: `{code: 0, data: {name, face, level, fans, following, regtime, joinDays, videos, ...}, error: null}`
- 失败: `{code: -1, data: null, error: "..."}` — 风控/不存在/超时/参数非法

### POST /api/analyze
- Body: `{uid, profile?}` (profile 可选，缺失时自动拉取)
- 成功: `{code: 0, data: {personaType, pastLife, mentalState, fortune2026, soulMate, danmuStyle, craziness}, error: null}`
- 失败: `{code: -1, data: null, error: "..."}`
- 超时: 180s (LLM reasoning 模型首 token 较慢)

### GET /api/rank?type=craziness&page=1&limit=20
- 返回: `{code: 0, data: {list: [...], total, type, page, limit, timestamp}, error: null}`

## LLM 容错策略 (`api/_llm.py`)

1. `response_format=json_object` 强制 JSON 输出
2. `max_tokens=6000` — 留够预算给 7 模块完整 JSON
3. HTTP timeout=45s，最多重试 3 次 (指数退避 1s→2s→4s + jitter)
4. 仅重试 5xx/429/空 choices/空 content/JSON 解析失败；4xx 不重试
5. JSON 容错：直接 parse → markdown 围栏剥离 → 平衡 `{}` 块提取 → 兜底默认值
6. Prompt 强约束：system prompt 明确写"直接输出 JSON，不要解释"

## 设计系统

- 移动端优先，最大宽度 640px，桌面端居中
- 主色 `#FB7299` (B站粉)，辅色 `#00AEEC` (B站蓝)，强调色 `#F5C842`
- 背景 `#F4F4F5`，卡片白底圆角 16px
- 字体：系统字体 + 得意黑 (CDN)
- Neo-Brutalist 硬投影
- 7 条弹幕飘过背景 (danmu.js 定时轮播)
- 分享卡: 1080×N PNG，鉴定证书视觉 (html2canvas + `/api/avatar` 代理)

## 注意点

- **B站风控 (-352)**: 频繁请求可能触发，建议 1-2 秒间隔
- **regtime 为 0**: 部分老账号返回 0，前端显示"元老级"
- **Netlify 文件系统只读**: `data/rank.json` 部署后无法写入，需 Vercel KV 或 Upstash Redis
- **头像跨域**: html2canvas 需要 `/api/avatar` 代理，直接访问 B站 CDN 会因 CORS 失败
- **UID 长度**: B站 2023 年后最长 18 位
- **PowerShell 启动**: 用 `$env:PYTHONIOENCODING="utf-8"` 避免 GBK 编码错误