/* =====================================================
 * cache.js — UID 缓存
 *  - 键名: cyber-judge:cache:{uid}
 *  - TTL:   24 小时
 *  - LRU:   最多 10 个 UID，超出按时间淘汰最旧
 *  - 全局命名空间 window.CyberJudgeCache
 *  - 兼容 Safari 隐私模式(localStorage 抛 SecurityError)
 * ===================================================== */
(function (global) {
  'use strict';

  var NS = 'cyber-judge';
  var KEY_PREFIX = NS + ':cache:';
  var INDEX_KEY = NS + ':cache-index';
  var TTL_MS = 24 * 60 * 60 * 1000; // 24 小时
  var MAX_ENTRIES = 10;

  function now() { return Date.now(); }

  function safeParse(json, fallback) {
    try { return JSON.parse(json); } catch (_) { return fallback; }
  }

  // ---------------------------------------------------------------------------
  // localStorage 可用性探测 (Safari 隐私模式 setItem 会抛 SecurityError)
  // ---------------------------------------------------------------------------
  var _storageOk = (function () {
    try {
      var k = NS + ':probe-' + now();
      global.localStorage.setItem(k, '1');
      global.localStorage.removeItem(k);
      return true;
    } catch (_) {
      return false;
    }
  })();

  function lsGet(key) {
    if (!_storageOk) return null;
    try { return global.localStorage.getItem(key); } catch (_) { return null; }
  }

  function lsSet(key, val) {
    if (!_storageOk) return false;
    try { global.localStorage.setItem(key, val); return true; } catch (_) { return false; }
  }

  function lsRemove(key) {
    if (!_storageOk) return;
    try { global.localStorage.removeItem(key); } catch (_) {}
  }

  function readIndex() {
    var raw = lsGet(INDEX_KEY);
    var arr = safeParse(raw, []);
    return Array.isArray(arr) ? arr : [];
  }

  function writeIndex(arr) {
    if (lsSet(INDEX_KEY, JSON.stringify(arr))) return;
    // 配额满:淘汰到只剩一半,同时清理对应 cache key 防止孤儿缓存
    var half = Math.floor(arr.length / 2);
    var removed = arr.slice(0, half);
    arr = arr.slice(half);
    // 防御 item.uid undefined(lsRemove 会拼成 'cyber-judge:cache:undefined',无害但脏)
    removed.forEach(function (item) {
      if (item && item.uid) lsRemove(KEY_PREFIX + item.uid);
    });
    // 二次尝试,失败则 log(便于排查 localStorage 异常)
    if (!lsSet(INDEX_KEY, JSON.stringify(arr))) {
      try { console.warn('[cache] index write failed twice, storage may be full or disabled'); } catch (_) {}
    }
  }

  function touchIndex(uid) {
    var arr = readIndex().filter(function (item) { return item.uid !== uid; });
    arr.push({ uid: uid, ts: now() });
    if (arr.length > MAX_ENTRIES) {
      // 淘汰最旧的
      var overflow = arr.length - MAX_ENTRIES;
      var removed = arr.splice(0, overflow);
      removed.forEach(function (item) { lsRemove(KEY_PREFIX + item.uid); });
    }
    writeIndex(arr);
  }

  function evictExpired() {
    var arr = readIndex();
    var alive = [];
    arr.forEach(function (item) {
      // 防御历史脏数据:item 缺 uid 或 ts 视为过期
      if (!item || !item.uid || typeof item.ts !== 'number') {
        if (item && item.uid) lsRemove(KEY_PREFIX + item.uid);
        return;
      }
      if (now() - item.ts <= TTL_MS) {
        alive.push(item);
      } else {
        lsRemove(KEY_PREFIX + item.uid);
      }
    });
    if (alive.length !== arr.length) writeIndex(alive);
  }

  function cacheGet(uid) {
    if (!uid) return null;
    evictExpired();
    var key = KEY_PREFIX + uid;
    var raw = lsGet(key);
    if (!raw) return null;
    var entry = safeParse(raw, null);
    if (!entry || typeof entry !== 'object') return null;
    // ts 必须是有效数字(0 是合法 timestamp,只拒绝非数字)
    if (typeof entry.ts !== 'number' || !isFinite(entry.ts)) return null;
    if (now() - entry.ts > TTL_MS) {
      lsRemove(key);
      return null;
    }
    // 数据完整性校验:必须有 profile + report 才有意义
    if (!entry.profile || !entry.report) {
      lsRemove(key);
      return null;
    }
    // 命中:刷新 LRU 时间戳
    touchIndex(uid);
    return entry;
  }

  function cacheSet(uid, report, profile) {
    if (!uid) return;
    var entry = { ts: now(), profile: profile, report: report };
    if (lsSet(KEY_PREFIX + uid, JSON.stringify(entry))) {
      touchIndex(uid);
      return;
    }
    // 写入失败:可能是配额满。先 evictExpired 腾空间再重试一次
    evictExpired();
    if (lsSet(KEY_PREFIX + uid, JSON.stringify(entry))) {
      touchIndex(uid);
    }
    // 仍然失败则静默忽略 (隐私模式 / 配额耗尽)
  }

  function cacheClear() {
    var arr = readIndex();
    arr.forEach(function (item) { lsRemove(KEY_PREFIX + item.uid); });
    lsRemove(INDEX_KEY);
  }

  function cacheSize() {
    return readIndex().length;
  }

  global.CyberJudgeCache = {
    get: cacheGet,
    set: cacheSet,
    clear: cacheClear,
    size: cacheSize,
    TTL_MS: TTL_MS,
    available: function () { return _storageOk; },
  };
})(window);
