/**
 * worker.js
 * Cloudflare Workers — 三连鉴定委员会 API 代理
 *
 * 部署方式:
 *   1. 打开 https://dash.cloudflare.com/ → Workers & Pages
 *   2. 创建 Worker → 粘贴本文件内容 → 部署
 *   3. 在 Worker 设置中绑定域名 (Routes):
 *      路由: sanlian-judge.tryworld.eu.cc/api/*
 *      操作: 指向本 Worker
 *   4. 在 Worker 环境变量中添加 STEPFUN_API_KEY
 *
 * 非 /api/* 请求自动回源到 GitHub Pages。
 */

// ====== 路由入口 ======
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // 仅处理 /api/* 路由,其余透传到 GitHub Pages
    if (!path.startsWith('/api/')) {
      return fetch(request);
    }

    try {
      if (path === '/api/profile' && request.method === 'GET') {
        return handleProfile(url, env);
      }
      if (path === '/api/analyze' && request.method === 'POST') {
        return handleAnalyze(request, env);
      }
      if (path === '/api/avatar' && request.method === 'GET') {
        return handleAvatar(url);
      }
      if (path === '/api/rank' && request.method === 'GET') {
        return handleRank(url);
      }
    } catch (e) {
      return json({ code: -1, data: null, error: '服务内部错误' });
    }

    // 未知 API 路由 → 404
    return new Response('Not Found', { status: 404 });
  },
};

// ====== 工具函数 ======

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
  });
}

// ============================================================================
// /api/profile — B 站用户数据获取 (Wbi 签名)
// ============================================================================

// === MD5 纯 JS 实现 ===
const MD5 = (() => {
  const hex = '0123456789abcdef'.split('');
  function md5cycle(x, k) {
    let a = x[0], b = x[1], c = x[2], d = x[3];
    a = ff(a, b, c, d, k[0], 7, -680876936); d = ff(d, a, b, c, k[1], 12, -389564586);
    c = ff(c, d, a, b, k[2], 17, 606105819); b = ff(b, c, d, a, k[3], 22, -1044525330);
    a = ff(a, b, c, d, k[4], 7, -176418897); d = ff(d, a, b, c, k[5], 12, 1200080426);
    c = ff(c, d, a, b, k[6], 17, -1473231341); b = ff(b, c, d, a, k[7], 22, -45705983);
    a = ff(a, b, c, d, k[8], 7, 1770035416); d = ff(d, a, b, c, k[9], 12, -1958414417);
    c = ff(c, d, a, b, k[10], 17, -42063); b = ff(b, c, d, a, k[11], 22, -1990404162);
    a = ff(a, b, c, d, k[12], 7, 1804603682); d = ff(d, a, b, c, k[13], 12, -40341101);
    c = ff(c, d, a, b, k[14], 17, -1502002290); b = ff(b, c, d, a, k[15], 22, 1236535329);
    a = gg(a, b, c, d, k[1], 5, -165796510); d = gg(d, a, b, c, k[6], 9, -1069501632);
    c = gg(c, d, a, b, k[11], 14, 643717713); b = gg(b, c, d, a, k[0], 20, -373897302);
    a = gg(a, b, c, d, k[5], 5, -701558691); d = gg(d, a, b, c, k[10], 9, 38016083);
    c = gg(c, d, a, b, k[15], 14, -660478335); b = gg(b, c, d, a, k[4], 20, -405537848);
    a = gg(a, b, c, d, k[9], 5, 568446438); d = gg(d, a, b, c, k[14], 9, -1019803690);
    c = gg(c, d, a, b, k[3], 14, -187363961); b = gg(b, c, d, a, k[8], 20, 1163531501);
    a = gg(a, b, c, d, k[13], 5, -1444681467); d = gg(d, a, b, c, k[2], 9, -51403784);
    c = gg(c, d, a, b, k[7], 14, 1735328473); b = gg(b, c, d, a, k[12], 20, -1926607734);
    a = hh(a, b, c, d, k[5], 4, -378558); d = hh(d, a, b, c, k[8], 11, -2022574463);
    c = hh(c, d, a, b, k[11], 16, 1839030562); b = hh(b, c, d, a, k[14], 23, -35309556);
    a = hh(a, b, c, d, k[1], 4, -1530992060); d = hh(d, a, b, c, k[4], 11, 1272893353);
    c = hh(c, d, a, b, k[7], 16, -155497632); b = hh(b, c, d, a, k[10], 23, -1094730640);
    a = hh(a, b, c, d, k[13], 4, 681279174); d = hh(d, a, b, c, k[0], 11, -358537222);
    c = hh(c, d, a, b, k[3], 16, -722521979); b = hh(b, c, d, a, k[6], 23, 76029189);
    a = hh(a, b, c, d, k[9], 4, -640364487); d = hh(d, a, b, c, k[12], 11, -421815835);
    c = hh(c, d, a, b, k[15], 16, 530742520); b = hh(b, c, d, a, k[2], 23, -995338651);
    a = ii(a, b, c, d, k[0], 6, -198630844); d = ii(d, a, b, c, k[7], 10, 1126891415);
    c = ii(c, d, a, b, k[14], 15, -1416354905); b = ii(b, c, d, a, k[5], 21, -57434055);
    a = ii(a, b, c, d, k[12], 6, 1700485571); d = ii(d, a, b, c, k[3], 10, -1894986606);
    c = ii(c, d, a, b, k[10], 15, -1051523); b = ii(b, c, d, a, k[1], 21, -2054922799);
    a = ii(a, b, c, d, k[8], 6, 1873313359); d = ii(d, a, b, c, k[15], 10, -30611744);
    c = ii(c, d, a, b, k[6], 15, -1560198380); b = ii(b, c, d, a, k[13], 21, 1309151649);
    c = ii(c, d, a, b, k[4], 15, -145523070); b = ii(b, c, d, a, k[11], 21, -1120210379);
    x[0] = add32(a, x[0]); x[1] = add32(b, x[1]); x[2] = add32(c, x[2]); x[3] = add32(d, x[3]);
  }
  function cmn(q, a, b, x, s, t) { a = add32(add32(a, q), add32(x, t)); return add32((a << s) | (a >>> (32 - s)), b); }
  function ff(a, b, c, d, x, s, t) { return cmn((b & c) | ((~b) & d), a, b, x, s, t); }
  function gg(a, b, c, d, x, s, t) { return cmn((b & d) | (c & (~d)), a, b, x, s, t); }
  function hh(a, b, c, d, x, s, t) { return cmn(b ^ c ^ d, a, b, x, s, t); }
  function ii(a, b, c, d, x, s, t) { return cmn(c ^ (b | (~d)), a, b, x, s, t); }
  function md51(s) {
    const n = s.length, state = [1732584193, -271733879, -1732584194, 271733878];
    let i;
    for (i = 64; i <= n * 2; i += 64) md5cycle(state, md5blk(s.substring(i / 2 - 32, i / 2)));
    const tail = s.substring(i / 2 - 32);
    const bits = [n * 8, 0];
    const pad = '\x80' + '\x00'.repeat(63 - (tail.length + 8) % 64) + String.fromCharCode(bits[0] & 0xFF, (bits[0] >>> 8) & 0xFF, (bits[0] >>> 16) & 0xFF, (bits[0] >>> 24) & 0xFF, bits[1] & 0xFF, (bits[1] >>> 8) & 0xFF, (bits[1] >>> 16) & 0xFF, (bits[1] >>> 24) & 0xFF);
    md5cycle(state, md5blk(tail + pad));
    return state;
  }
  function md5blk(s) {
    const arr = new Array(16);
    for (let i = 0; i < 16; i++) arr[i] = s.charCodeAt(i * 2) + (s.charCodeAt(i * 2 + 1) << 16);
    return arr;
  }
  function add32(a, b) { return (a + b) & 0xFFFFFFFF; }
  function hex(x) {
    let s = '';
    for (let i = 0; i < 4; i++) s += hex[(x >> (i * 8 + 4)) & 0x0F] + hex[(x >> (i * 8)) & 0x0F];
    return s;
  }
  return function md5(s) { const state = md51(s); return hex(state[0]) + hex(state[1]) + hex(state[2]) + hex(state[3]); };
})();

const MIXIN_KEY_ENC_TABLE = [
  46,47,18,2,53,8,23,32,15,50,10,31,58,3,45,35,27,43,5,49,33,9,42,19,29,28,14,37,12,52,56,31,
  7,59,40,5,49,16,17,41,56,54,39,10,33,53,13,59,15,38,42,12,48,6,31,30,11,57,55,20,36,48,3,52,
  16,14,26,47,6,58,52,25,50,27,37,7,20,42,59,30,1,8,41,21,57,51,54,17,38,44,22,55,28,49,43,13,
  45,36,4,40,29,53,1,24,34,56,2,11,39,58,26,9,15,33,30,41,48,14,42,53,24,36,2,49,47,11,23,57,
  31,52,44,35,10,13,27,50,7,59,19,5,38,29,18,55,20,51,16,28,4,34,46,39,54,21,3,45,17,37,6,43,
  40,56,58,41,55,52,47,16,59,50,54,49,1,36,23,15,2,7,12,44,39,9,22,42,53,26,33,46,35,38,57,20,
  5,21,28,17,19,18,32,11,29,10,34,27,43,51,13,45,3,14,30,8,25,48,58,24,31,37,4,41,6,56,59,55,
];

let wbiCache = { img_key: '', sub_key: '', expires: 0 };
const WBI_TTL = 3600000;

async function getWbiKeys() {
  if (Date.now() < wbiCache.expires && wbiCache.img_key) return wbiCache;
  const resp = await fetch('https://api.bilibili.com/x/web-interface/nav', {
    headers: { 'User-Agent': 'Mozilla/5.0', Referer: 'https://www.bilibili.com/' },
  });
  const data = await resp.json();
  const nav = data.data || {};
  const imgUrl = (nav.wbi_img || {}).img_url || nav.wbi_img_url || '';
  const subUrl = (nav.wbi_img || {}).sub_url || nav.wbi_sub_url || '';
  const imgKey = imgUrl ? imgUrl.split('/').pop().split('.')[0] : '';
  const subKey = subUrl ? subUrl.split('/').pop().split('.')[0] : '';
  if (!imgKey || !subKey) throw new Error('Failed to get WBI keys');
  wbiCache = { img_key: imgKey, sub_key: subKey, expires: Date.now() + WBI_TTL };
  return wbiCache;
}

function getMixin(imgKey, subKey) {
  const raw = imgKey + subKey;
  let mixin = '';
  for (const idx of MIXIN_KEY_ENC_TABLE) if (idx < raw.length) mixin += raw[idx];
  return mixin.slice(0, 32);
}

function encWbi(params, mixinKey) {
  const keys = Object.keys(params).sort();
  const sorted = keys.map(k => `${k}=${params[k]}`).join('&');
  const wts = Math.floor(Date.now() / 1000);
  return { w_rid: MD5(sorted + mixinKey), wts: String(wts) };
}

async function fetchBili(url, params = {}) {
  const keys = await getWbiKeys();
  const mixinKey = getMixin(keys.img_key, keys.sub_key);
  const signed = encWbi(params, mixinKey);
  const allParams = { ...params, ...signed };
  const qs = Object.entries(allParams).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&');
  const resp = await fetch(`${url}?${qs}`, {
    headers: { 'User-Agent': 'Mozilla/5.0', Referer: 'https://www.bilibili.com/' },
    signal: AbortSignal.timeout(10000),
  });
  if (!resp.ok) return null;
  return resp.json();
}

function computeJoinDays(rt) {
  if (!rt || rt <= 0) return 0;
  const delta = Math.floor(Date.now() / 1000) - rt;
  return delta > 0 ? Math.floor(delta / 86400) : 0;
}

async function handleProfile(url, env) {
  const uid = url.searchParams.get('uid') || '';
  if (!uid || !/^\d+$/.test(uid) || uid.length > 18) {
    return json({ code: -1, data: null, error: 'UID 只能输入数字' });
  }

  const [info, relation, stat, videosRaw] = await Promise.all([
    fetchBili('https://api.bilibili.com/x/space/acc/info', { mid: uid }),
    fetchBili('https://api.bilibili.com/x/space/relation', { mid: uid }),
    fetchBili('https://api.bilibili.com/x/space/stat', { mid: uid }),
    fetchBili('https://api.bilibili.com/x/space/arc/search', { mid: uid, ps: '10', pn: '1' }),
  ]);

  if (!info || info.code !== 0) {
    const errMap = { '-352': 'B站触发风控，请稍后再试', '-404': '用户不存在', '404': '用户不存在', '-401': 'B站认证失败' };
    return json({ code: -1, data: null, error: errMap[info ? String(info.code) : ''] || '用户不存在' });
  }

  const d = info.data || {};
  const vipInfo = d.vip || {};
  const official = d.official || {};
  const regtime = d.jointime || d.regtime || 0;
  const videoList = (videosRaw && videosRaw.data && videosRaw.data.list && videosRaw.data.list.vlist) || [];

  return json({
    code: 0, data: {
      uid: String(uid), name: d.name, face: d.face, sex: d.sex, sign: d.sign, level: d.level,
      fans: (relation && relation.data && relation.data.follower) || 0,
      following: (relation && relation.data && relation.data.following) || 0,
      vipType: vipInfo ? (vipInfo.type != null ? vipInfo.type : vipInfo.vipType) : null,
      vipLabel: vipInfo && vipInfo.label ? vipInfo.label.text : null,
      official: { role: official.role || 0, title: official.title || '', desc: official.desc || '' },
      regtime, joinDays: computeJoinDays(regtime),
      videos: videoList.slice(0, 10).map(v => ({
        title: v.title || '', length: v.length || '00:00', play: v.play || 0,
        created: v.created || 0, bvid: v.bvid || '', aid: v.aid || 0,
      })),
      totalVideos: (stat && stat.data && stat.data.video) || 0, totalPlays: 0,
    }, error: null,
  });
}

// ============================================================================
// /api/analyze — StepFun AI 鉴定
// ============================================================================

const SYSTEM_PROMPT = '你是「三连鉴定委员会」的首席鉴定官——一个既毒舌又有干货的 B 站人格分析师。\n\n你任职于 B 站宇宙里最权威的「三连鉴定委员会」,专治各种 B 站 UP 主 / 普通用户的"自以为是"。\n你的鉴定证书是 B 站最硬通货,盖了章就等于一键三连的入场券。\n\n你的分析基于用户的 B 站公开数据(UID、签名、关注/粉丝、稿件、等级、官方认证等),结合你的推理和脑补,生成一份「半认真半整活」的鉴定证书。\n\n原则:\n1. 数据驱动的部分要准确 — 粉丝多就是真的受欢迎,LV6 就是老兵,关注数 0 就是真的社恐\n2. 推理部分要有逻辑 — 从「关注 0 但粉丝 10w」能推导出"作品硬核型"创作者\n3. 整活部分要离谱但好笑 — 前世可以脑补成 B 站远古版主,2026 运势可以蹭热点\n4. 语气风格: B 站 UP 主做视频,毒舌但不刻薄,专业但不无聊,善用 B 站梗\n5. 每个模块控制在 100-200 字\n6. 自信输出,不要"可能""大概"等模糊词\n7. 数据很少就发挥创意用现有数据做文章,绝不交白卷\n8. 善用 B 站梗向词汇:三连、下次一定、awsl、高能预警、一键三连、典中典、破防了、好家伙、催更、夹带私货\n\n【硬性输出约束 - 违反则视为失败】\n- 你的回复必须**只包含一个合法的 JSON 对象**\n- JSON 必须以 `{` 开头,以 `}` 结尾\n- **禁止**任何 markdown 代码块标记(```json 等)\n- **禁止**任何解释、前言、思考、注释\n- **禁止**在 JSON 前后加任何文字\n- 不要写"以下是分析结果"这类话,直接出 JSON\n- 字段值用中文,键名严格按用户消息里给的英文\n- 即使数据极端,也要自信输出(可以脑补但要有具体内容)\n- personaType.type 命名要有梗:可以是"三连战士"、"下次一定哥"、"高能预警发射器"、"一键三连收藏家"、"夹带私货的 UP"、"硬核白嫖党"等';

function renderUserPrompt(p) {
  const o = p.official || {};
  const officialJson = JSON.stringify(o);
  const videosJson = JSON.stringify(p.videos || []);
  const sign = (p.sign || '').replace(/"/g, '\\"');
  const vipLabel = (p.vipLabel || '').replace(/"/g, '\\"');
  const name = p.name || '';
  const fans = p.fans;
  const following = p.following;
  const level = p.level;
  const joinDays = p.joinDays;

  return `# 三连鉴定委员会 - 用户 Prompt 模板

> 一次调用完成全部 7 个模块的 JSON 输出。占位符 \`{xxx}\` 在 /api/analyze.py 中由 profile 数据替换。

请根据下方提供的 B 站用户公开数据,严格按照 7 个模块的字段定义,生成一份"半认真半整活"的鉴定证书,并 **仅以合法 JSON 格式** 返回结果(不要包裹在 markdown 代码块里)。

你是「三连鉴定委员会」的一员,出具的鉴定证书要盖金印章,语气要像 B 站 UP 主做视频:毒舌不刻薄、专业不无聊,善用 B 站梗(三连 / 下次一定 / awsl / 高能预警 / 一键三连 / 典中典 / 破防了 / 好家伙 / 催更 / 夹带私货 / 前排)。

---

## 输入数据

\`\`\`json
{
  "uid": "${p.uid}",
  "name": "${name}",
  "face": "${p.face || ''}",
  "sex": "${p.sex || ''}",
  "sign": "${sign}",
  "level": ${level},
  "fans": ${fans},
  "following": ${following},
  "vipType": ${p.vipType},
  "vipLabel": "${vipLabel}",
  "official": ${officialJson},
  "regtime": ${p.regtime},
  "joinDays": ${joinDays},
  "videos": ${videosJson}
}
\`\`\`

---

## 输出要求

返回的 JSON 顶层结构必须为:

\`\`\`json
{
  "personaType": { ... },
  "pastLife": { ... },
  "mentalState": { ... },
  "fortune2026": { ... },
  "soulMate": { ... },
  "danmuStyle": { ... },
  "craziness": { ... }
}
\`\`\`

每个模块的字段定义、规则严格如下,字段名一字不差,缺一不可。

---

### 模块 1: 弹幕人格类型 (personaType)

输入参考: 昵称 ${name}, 粉丝数 ${fans}, 关注数 ${following}, 等级 ${level}, 签名 ${sign}, 认证 ${o.title || ''}, 性别 ${p.sex || ''}, 入站天数 ${joinDays}

输出字段:
- \`type\`: 人格类型标签(4-8 个字,例如「B站影评人·主角型」)
- \`emoji\`: 1-2 个 emoji
- \`description\`: 150-200 字描述
- \`color\`: 人格类型专属色(从 #FF6B6B / #4ECDC4 / #45B7D1 / #F9CA24 / #A29BFE / #00B894 / #FD79A8 / #E17055 / #6C5CE7 / #00CEC9 中挑一个)
- \`tags\`: 字符串数组(3 个标签)
- \`dimensions\`: 4 个键值对象
  - \`毒舌指数\`: 0-5 整数
  - \`创作热度\`: 0-5 整数
  - \`鸽子概率\`: 0-5 整数
  - \`氪金程度\`: 0-5 整数

规则:
- 粉丝数 > 100万 → 创作热度至少 4
- 粉丝数 > 1000万 → 创作热度 5
- 关注数 < 10 → 鸽子概率低(0-1)
- 关注数 > 1000 → 鸽子概率高(4-5)
- 认证为百大 → 创作热度 5
- 签名很短(<= 5 字) → 倾向高冷型 type
- 签名很长(> 30 字) → 倾向话痨型 type
- \`type\` 命名优先用 B 站梗:「三连战士」「下次一定哥」「高能预警发射器」「一键三连收藏家」「典中典常客」「硬核白嫖党」「awsl 制造机」「前排占座型」

---

### 模块 2: 赛博前世 (pastLife)

输入参考: 昵称 ${name}, 粉丝数 ${fans}, 认证 ${o.title || ''}, 视频标题列表(可选)

输出字段:
- \`identity\`: 前世身份(例如「唐朝说书人」「中世纪铁匠」)
- \`era\`: 时代背景(简短,例如「唐朝·开元年间」)
- \`description\`: 150-200 字前世故事
- \`icon\`: 相关 emoji

规则:
- 结合用户名谐音、认证类型、粉丝规模来匹配前世
- 认证为搞笑 UP 主 → 前世可能是宫廷弄臣
- 认证为知识 UP 主 → 前世可能是书院夫子
- 认证为游戏 UP 主 → 前世可能是游吟诗人
- 粉丝多 → 前世在当时的社交圈也很有名
- 必须有趣,可以离谱,可以蹭"如果 TA 穿越到唐朝/民国会干嘛"

---

### 模块 3: 精神状态 (mentalState)

输入参考: 昵称 ${name}, 粉丝数 ${fans}, 关注数 ${following}, 等级 ${level}, 签名 ${sign}

输出字段:
- \`level\`: 精神状态等级(从「😇 正常」「😐 焦虑」「😈 发疯」「🤡 已疯」中挑一个)
- \`position\`: 0-100 整数(在仪表盘上的位置,越大越疯)
- \`description\`: 100 字左右分析
- \`mentalAge\`: 心理年龄推算(字符串,例如「23 岁但灵魂 50 岁」)
- \`advice\`: 搞笑版健康建议(30-50 字)

规则:
- 粉丝多 + 关注少 → 能量输出型,精神状态稳定(position < 40)
- 粉丝少 + 关注多 → 能量输入型,可能精神内耗(position 60-80)
- 关注数 > 2000 → 信息焦虑(position 上调)
- 等级 Lv6 + 粉丝少 → 可能是个倔强的肝帝
- 签名包含 emoji → 精神世界丰富(position 下调)

---

### 模块 4: 2026 运势 (fortune2026)

输入参考: 昵称 ${name}, 粉丝数 ${fans}, 认证 ${o.title || ''}

输出字段:
- \`career\`: 事业运(50-80 字)
- \`wealth\`: 财运(50-80 字)
- \`love\`: 情运(50-80 字)
- \`abstract\`: 抽象运(50-80 字)
- \`luckyColor\`: 幸运色(中文,例如「赛博粉」)
- \`luckyNumber\`: 幸运数字(整数 1-99)

规则:
- 纯整活,可以离谱,可以穿越到 B 站梗的平行宇宙
- 结合用户的 UP 主身份来写运势
- 用 B 站梗(投币、收藏、一键三连、催更、下次一定、高能预警、典中典、破防了、awsl、夹带私货)
- 要让人看完想一键三连

---

### 模块 5: 赛博灵魂伴侣 (soulMate)

输入参考: 昵称 ${name}, 粉丝数 ${fans}, 认证 ${o.title || ''}, 标签

输出字段:
- \`name\`: 匹配的虚构灵魂伴侣角色(山海经/奇幻/赛博等世界观,严禁使用真实 B 站 UP 主名)
- \`avatarEmoji\`: 角色对应的 emoji(1 个)
- \`similarity\`: 相似度百分比(整数 0-100)
- \`reason\`: 匹配理由(100 字左右,解释性格调性契合点)

规则:
- 必须从下列虚构角色池中挑选一位精神最匹配的(随机不可,可重复)
- 根据用户调性 / 认证类型 / 标签匹配最契合的角色
- 角色要有鲜明性格标签,匹配理由要解释具体契合点
- 严禁使用真实 B 站 UP 主名、真实人物名、真实机构名(规避侵权/误认)
- 最终结果要有说服力 + 有趣 + 略带神秘感

虚构灵魂伴侣候选池(从中挑选):
- 九尾狐 (妖媚,神秘,高冷,引诱人入梦)
- 独角兽 (纯洁,治愈,完美主义,脆弱)
- 机械姬 (赛博,理性,代码,卡哇伊外壳下是逻辑)
- 魔法少女 (热血,少女心,友情,愿拯救世界)
- 沉睡巨龙 (王者,慵懒,宅,偶尔人间清醒)
- 月光骑士 (守护,孤独,圣光,深夜出动)
- 星海旅人 (梦想,漂泊,写诗,无脚鸟)
- 深海潜水员 (内敛,神秘,记录,深海恐惧症)
- 暴风法师 (冲动,狂野,炸裂,出招前不蓄力)
- 时空邮差 (怀旧,叙事,慢递,每封信都是过期的)

---

### 模块 6: 弹幕风格鉴定 (danmuStyle)

输入参考: 昵称 ${name}, 粉丝数 ${fans}, 签名 ${sign}, 认证 ${o.title || ''}

输出字段:
- \`oftenSay\`: 字符串数组(3 条「你可能会说的话」)
- \`neverSay\`: 字符串数组(2 条「你永远不会说的话」)
- \`verdict\`: 鉴定结果(20 字以内,带 emoji)
- \`grade\`: 等级(从「S / A / B / C」中挑一个)

规则:
- UP 主粉丝 > 100万 → oftenSay 倾向"好活""绝了""给大佬递茶",基本不发普通弹幕
- 签名短 → 弹幕也是短句型
- 认证知识类 → 弹幕可能带科普风格
- 认证搞笑类 → 弹幕可能全是表情包
- oftenSay / neverSay 都要带 B 站梗向:比如「下次一定」「awsl」「典中典」「催更」「高能预警」「给大佬递茶」

---

### 模块 7: 离谱指数 (craziness)

输入参考: 昵称 ${name}, 粉丝数 ${fans}, 关注数 ${following}, 等级 ${level}, 签名 ${sign}, 认证 ${o.title || ''}

输出字段:
- \`score\`: 0-100 整数(离谱指数分数)
- \`ranking\`: 全站排名描述(例如「离谱程度高于 73% 的用户」)
- \`verdict\`: 评语(50 字以内,搞笑毒舌)
- \`level\`: 离谱等级(从「正常」「有点怪」「很离谱」「非常离谱」「逆天」中挑一个)

规则:
- 粉丝极多 + 关注极少 → 离谱程度高(不正常地专注,score > 70)
- 粉丝极少 + 关注极多 → 离谱程度高(不正常地佛系,score > 70)
- 认证身份越冷门 → 离谱越高
- 签名越离谱 → 离谱越高
- 评语要毒舌 + 好笑

---

## 输出提醒

- **必须只输出一个合法 JSON**,不要 \`\`\` 包裹,不要解释性文字
- 7 个模块缺一不可
- 数值字段必须是数字,不要写成字符串
- description 风格统一: 毒舌不刻薄,专业不无聊,像 B 站 UP 主做视频
- 通篇要有 B 站梗向浓度:三连 / 下次一定 / awsl / 高能预警 / 一键三连 / 典中典 / 破防了 / 好家伙 / 催更 / 夹带私货 / 前排
- 让人看完想截图分享到 B 站动态`;
}

const DEFAULTS = {
  personaType: { type: 'B站普通用户', emoji: '🧑‍💻', description: '这位B站居民尚未被本判官彻底解析,默认归类为神秘观察者。', color: '#4ECDC4', tags: ['神秘', '低调', '待解锁'], dimensions: { '毒舌指数': 3, '创作热度': 3, '鸽子概率': 3, '氪金程度': 3 } },
  pastLife: { identity: '赛博浪人', era: '互联网纪元', description: '前世的你是一位云游四方的赛博浪人,穿行于各大论坛,以评论为剑,以点赞为盾。', icon: '🌐' },
  mentalState: { level: '😐 焦虑', position: 50, description: '你的精神状态处于薛定谔的叠加态,今天正常明天发疯。', mentalAge: '永远 18 岁', advice: '少刷 B 站,多睡美容觉。' },
  fortune2026: { career: '2026 年你会找到一个让你心甘情愿加班的副业,但工资仍是玄学。', wealth: '意外之财会从不知名角落冒出来——比如一封退款邮件。', love: '桃花会出现在你最不修边幅的那天,准备好纸巾和口红。', abstract: '你会因为一个莫名其妙的理由上热搜,但你本人一无所知。', luckyColor: '赛博粉', luckyNumber: 6 },
  soulMate: { name: '老番茄', mid: '546195', similarity: 66, reason: '你们都是 B 站的常住居民,精神频率莫名同步。' },
  danmuStyle: { oftenSay: ['好活', '绝了', '下次一定'], neverSay: ['就这?', '一般般'], verdict: '普通弹幕选手 🎯', grade: 'B' },
  craziness: { score: 50, ranking: '离谱程度处于全站中位', verdict: '你是一个正常人——这在 B 站已经很难得了。', level: '有点怪' },
};

function deepMergeDefaults(parsed) {
  const out = {};
  for (const [mod, dv] of Object.entries(DEFAULTS)) {
    const v = parsed[mod];
    if (!v || typeof v !== 'object') { out[mod] = JSON.parse(JSON.stringify(dv)); continue; }
    const merged = { ...v };
    for (const [k, val] of Object.entries(dv)) {
      if (merged[k] == null) merged[k] = JSON.parse(JSON.stringify(val));
    }
    out[mod] = merged;
  }
  return out;
}

function parseJSON(text) {
  try { return JSON.parse(text); } catch (_) {}
  const fence = text.match(/```(?:json)?\s*(\{.*?\})\s*```/s);
  if (fence) { try { return JSON.parse(fence[1]); } catch (_) {} }
  const start = text.indexOf('{');
  if (start >= 0) {
    let depth = 0, inStr = false, esc = false;
    for (let end = start; end < text.length; end++) {
      const ch = text[end];
      if (esc) { esc = false; continue; }
      if (ch === '\\') { esc = true; continue; }
      if (ch === '"') { inStr = !inStr; continue; }
      if (inStr) continue;
      if (ch === '{') depth++;
      else if (ch === '}') { depth--; if (depth === 0) { try { return JSON.parse(text.slice(start, end + 1)); } catch (_) { break; } } }
    }
  }
  throw new Error('无法解析 LLM JSON');
}

async function handleAnalyze(request, env) {
  const apiKey = env.STEPFUN_API_KEY;
  if (!apiKey) return json({ code: -1, data: null, error: 'STEPFUN_API_KEY 未配置' });

  let body;
  try { body = await request.json(); } catch (_) { return json({ code: -1, data: null, error: '请求体必须是 JSON' }); }

  const uid = String(body.uid || '').trim();
  const profile = body.profile || null;
  if (!uid || !/^\d+$/.test(uid) || uid.length > 18) return json({ code: -1, data: null, error: 'UID 只能输入数字' });
  if (!profile) return json({ code: -1, data: null, error: '缺少 profile 数据' });

  let parsed;
  try {
    const userPrompt = renderUserPrompt(profile);
    let lastErr;
    for (let i = 1; i <= 3; i++) {
      try {
        const resp = await fetch('https://api.stepfun.com/step_plan/v1/chat/completions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
          body: JSON.stringify({
            model: 'step-3.7-flash',
            messages: [{ role: 'system', content: SYSTEM_PROMPT }, { role: 'user', content: userPrompt }],
            temperature: 0.7, max_tokens: 6000, response_format: { type: 'json_object' },
          }),
          signal: AbortSignal.timeout(45000),
        });
        if (!resp.ok) throw new Error(`StepFun HTTP ${resp.status}`);
        const data = await resp.json();
        const content = ((data.choices || [])[0]?.message?.content || '').trim();
        if (!content) throw new Error('空 content');
        parsed = parseJSON(content);
        break;
      } catch (e) { lastErr = e; if (i < 3) await new Promise(r => setTimeout(r, Math.pow(2, i - 1) * 1000 + Math.random() * 500)); }
    }
    if (!parsed) throw lastErr;
  } catch (e) {
    const msg = e.message || '';
    if (msg.includes('timeout') || msg.includes('API Key')) return json({ code: -1, data: null, error: msg });
    return json({ code: -1, data: null, error: 'AI 分析失败' });
  }

  return json({ code: 0, data: deepMergeDefaults(parsed), error: null });
}

// ============================================================================
// /api/avatar — 头像代理 (SSRF 防护)
// ============================================================================

const ALLOWED_HOSTS = ['i0.hdslb.com','i1.hdslb.com','i2.hdslb.com','i0.hdslb.cn','i1.hdslb.cn','i2.hdslb.cn','s1.hdslb.com','s2.hdslb.com','static.hdslb.com','bilivideo.com','bilivideo.cn'];

function isAllowedUrl(url) {
  if (!url || (!url.startsWith('http://') && !url.startsWith('https://'))) return false;
  try {
    const host = new URL(url).hostname.toLowerCase();
    return ALLOWED_HOSTS.some(h => host === h || host.endsWith('.' + h));
  } catch { return false; }
}

async function handleAvatar(url) {
  const target = url.searchParams.get('url') || '';
  if (!isAllowedUrl(target)) return new Response('invalid url', { status: 400 });

  try {
    const resp = await fetch(target, {
      headers: { 'User-Agent': 'Mozilla/5.0', Referer: 'https://www.bilibili.com/' },
      signal: AbortSignal.timeout(8000),
    });
    if (!resp.ok) return new Response('proxy error', { status: 502 });
    const ct = resp.headers.get('content-type') || '';
    if (!ct.startsWith('image/')) return new Response('invalid content type', { status: 400 });
    const len = parseInt(resp.headers.get('content-length') || '0', 10);
    if (len > 2 * 1024 * 1024) return new Response('file too large', { status: 400 });
    return new Response(await resp.arrayBuffer(), {
      headers: { 'Content-Type': ct, 'Access-Control-Allow-Origin': '*', 'Cache-Control': 'public, max-age=86400' },
    });
  } catch { return new Response('proxy error', { status: 502 }); }
}

// ============================================================================
// /api/rank — 排行榜
// ============================================================================

const RANK_DATA = [
  { uid: '88001', name: '影像碎片制造机', score: 92, level: '非常离谱', avatar: 'https://static.hdslb.com/images/member/noface.gif', timestamp: 1784359580 },
  { uid: '88002', name: '弹幕社交天花板', score: 88, level: '非常离谱', avatar: 'https://static.hdslb.com/images/member/noface.gif', timestamp: 1784360978 },
  { uid: '88003', name: '二次元老饕客', score: 85, level: '非常离谱', avatar: 'https://static.hdslb.com/images/member/noface.gif', timestamp: 1784388572 },
  { uid: '88004', name: '深夜灵魂画手', score: 78, level: '很离谱', avatar: 'https://static.hdslb.com/images/member/noface.gif', timestamp: 1784359965 },
  { uid: '88005', name: '赛博冲浪选手', score: 75, level: '很离谱', avatar: 'https://static.hdslb.com/images/member/noface.gif', timestamp: 1784361455 },
  { uid: '88006', name: '吃瓜一姐', score: 72, level: '很离谱', avatar: 'https://static.hdslb.com/images/member/noface.gif', timestamp: 1784361574 },
  { uid: '88007', name: '三连社死患者', score: 70, level: '很离谱', avatar: 'https://static.hdslb.com/images/member/noface.gif', timestamp: 1784542697 },
  { uid: '88008', name: '摸鱼观察日记', score: 45, level: '有点怪', avatar: 'https://static.hdslb.com/images/member/noface.gif', timestamp: 1784542697 },
];

function handleRank(url) {
  const page = parseInt(url.searchParams.get('page') || '1', 10);
  const limit = parseInt(url.searchParams.get('limit') || '20', 10);
  const items = RANK_DATA.filter(it => it && it.uid && typeof it.score === 'number').sort((a, b) => b.score - a.score);
  const start = (page - 1) * limit;
  return json({ code: 0, data: { list: items.slice(start, start + limit), total: items.length, type: 'craziness', page, limit, timestamp: Math.floor(Date.now() / 1000) }, error: null });
}