#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam 优惠精选 — 单文件解决方案
=================================
使用方法:
    python steam-deals.py
    或双击 启动.bat

隐私安全:
    - 服务器仅监听 127.0.0.1 (本机), 外部网络无法访问
    - 所有数据请求由浏览器直接发给 CheapShark / Steam API
    - 不收集、不上传任何用户数据、本地文件或 Steam 账号信息
    - 不需要 Steam 登录, 不携带任何 Cookie / Token
    - 源码公开, 可自行审查

运行机制:
    双击运行 → 自动打开浏览器 → 关闭页面后自动退出 → 不留后台进程
"""
import http.server
import threading
import webbrowser
import time
import sys
import os

# Windows 控制台 UTF-8 兼容
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ============================================================
# 内嵌 HTML 页面
# ============================================================
HTML_PAGE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎮 Steam 优惠精选</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg-primary: #1a1c23;
  --bg-card: #21242d;
  --bg-card-hover: #2a2e3a;
  --accent: #1a9fff;
  --accent-glow: rgba(26, 159, 255, 0.15);
  --green: #5c7;
  --orange: #fa3;
  --red: #e55;
  --text: #ddd;
  --text-dim: #999;
  --text-bright: #fff;
  --radius: 12px;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg-primary);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.5;
}

.header {
  background: linear-gradient(135deg, #1a1c23 0%, #1e3a5f 50%, #1a1c23 100%);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  padding: 28px 20px 20px;
  text-align: center;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(20px);
}

.header h1 { font-size: 1.8rem; color: var(--text-bright); margin-bottom: 2px; }
.header .subtitle { color: var(--text-dim); font-size: 0.85rem; }

/* status indicator */
.status-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  background: var(--green);
  animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* sort bar */
.sort-bar {
  display: flex; justify-content: center; gap: 4px;
  padding: 14px 20px 0;
  position: sticky; top: 100px; z-index: 99;
  background: var(--bg-primary);
}

.sort-btn {
  padding: 9px 24px;
  border: 1px solid rgba(255,255,255,0.08);
  background: var(--bg-card); color: var(--text-dim);
  cursor: pointer; border-radius: 999px;
  font-size: 0.9rem; font-family: inherit;
  transition: 0.2s ease;
}

.sort-btn:hover { color: var(--text-bright); border-color: rgba(255,255,255,0.2); }
.sort-btn.active {
  background: var(--accent); color: #fff;
  border-color: var(--accent);
  box-shadow: 0 0 20px var(--accent-glow);
}

/* sections */
.container { max-width: 1400px; margin: 0 auto; padding: 20px; }

.section-title {
  font-size: 1.25rem; color: var(--text-bright);
  margin: 28px 0 14px; padding-left: 4px;
  display: flex; align-items: center; gap: 10px;
}

.section-title .badge {
  font-size: 0.72rem; background: var(--accent);
  color: #fff; padding: 3px 10px; border-radius: 999px; font-weight: 500;
}
.section-title .badge.today { background: var(--red); }

/* card grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 14px;
}

/* card */
.card {
  background: var(--bg-card); border-radius: var(--radius);
  overflow: hidden; cursor: pointer; text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
  position: relative; border: 1px solid transparent; display: block;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.4);
  background: var(--bg-card-hover);
  border-color: rgba(255,255,255,0.06);
}

.card-img-wrap {
  position: relative; width: 100%; padding-top: 40%;
  background: #1a1c23; overflow: hidden;
}

.card-img-wrap img {
  position: absolute; top: 0; left: 0;
  width: 100%; height: 100%; object-fit: cover;
}

.discount-badge {
  position: absolute; top: 8px; right: 8px;
  background: var(--green); color: #000;
  font-weight: 800; font-size: 0.78rem;
  padding: 3px 8px; border-radius: 6px; z-index: 2;
}
.discount-badge.deep { background: var(--red); color: #fff; }
.discount-badge.medium { background: #b3c935; color: #000; }

.deal-badge {
  position: absolute; bottom: 8px; left: 8px;
  background: rgba(0,0,0,0.75); color: var(--green);
  font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; z-index: 2;
}

.card-body { padding: 12px; }

.card-title {
  font-size: 0.88rem; font-weight: 600; color: var(--text-bright);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-bottom: 8px;
}

.card-pricing { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.price-original { font-size: 0.76rem; color: var(--text-dim); text-decoration: line-through; }
.price-sale { font-size: 0.95rem; font-weight: 700; color: var(--text-bright); }

.card-ratings { display: flex; align-items: center; gap: 8px; font-size: 0.73rem; flex-wrap: wrap; color: var(--text-dim); }
.rating-score { font-weight: 700; color: var(--text-bright); }
.rating-score.meta-high { color: #6cf; }
.rating-score.meta-mid { color: var(--orange); }
.rating-score.meta-low { color: var(--red); }
.release-date { color: var(--text-dim); font-size: 0.7rem; margin-top: 4px; }

/* top 3 glow */
.card-grid[data-ranked] .card:nth-child(1) { border-color: rgba(255,215,0,0.35); }
.card-grid[data-ranked] .card:nth-child(2) { border-color: rgba(192,192,192,0.25); }
.card-grid[data-ranked] .card:nth-child(3) { border-color: rgba(205,127,50,0.2); }

.rank-num {
  position: absolute; top: 6px; left: 8px;
  font-size: 1.3rem; font-weight: 900; color: #fff;
  text-shadow: 0 2px 6px rgba(0,0,0,0.6); z-index: 2;
}
.card:nth-child(1) .rank-num { color: #ffd700; }
.card:nth-child(2) .rank-num { color: #c0c0c0; }
.card:nth-child(3) .rank-num { color: #cd7f32; }

/* loading skeleton */
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 14px;
}
.skeleton-card { background: var(--bg-card); border-radius: var(--radius); overflow: hidden; animation: pulse 1.5s ease-in-out infinite; }
.skeleton-img { padding-top: 40%; background: #2a2e3a; }
.skeleton-body { padding: 12px; }
.skeleton-line { height: 14px; background: #2a2e3a; border-radius: 4px; margin-bottom: 8px; }
.skeleton-line.short { width: 60%; }
.skeleton-line.price { width: 40%; }

@keyframes pulse { 0%,100% {opacity:0.6} 50% {opacity:1} }
@keyframes pulse-badge { 0%,100% {opacity:1} 50% {opacity:0.6} }

/* error */
.error-msg {
  background: rgba(229,85,85,0.1); border: 1px solid rgba(229,85,85,0.3);
  border-radius: var(--radius); padding: 20px; text-align: center; color: var(--red); margin: 20px 0;
}
.error-msg button {
  margin-top: 12px; padding: 8px 24px; border: none;
  background: var(--accent); color: #fff; border-radius: 6px; cursor: pointer; font-family: inherit;
}

.last-updated { text-align: center; color: var(--text-dim); font-size: 0.76rem; padding: 28px 0 40px; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }

@media (max-width: 600px) {
  .header h1 { font-size: 1.3rem; }
  .sort-btn { padding: 7px 14px; font-size: 0.8rem; }
  .card-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }
  .card-body { padding: 10px; }
}
</style>
</head>
<body>

<header class="header">
  <h1><span class="status-dot" id="status-dot"></span>Steam 优惠精选</h1>
  <p class="subtitle">价格优先使用 Steam 中国区数据 · 部分游戏为 USD 估算 (标 ~ 或 ⚠)</p>
</header>

<nav class="sort-bar">
  <button class="sort-btn active" data-sort="popularity">🔥 按热度</button>
  <button class="sort-btn" data-sort="rating">⭐ 按评分</button>
  <button class="sort-btn" data-sort="price">💰 按价格</button>
</nav>

<div class="container" id="app">
  <section id="today-section">
    <div class="section-title">⚡ 今日特惠 <span class="badge today" id="today-badge">加载中</span></div>
    <div class="card-grid" id="today-grid"></div>
  </section>
  <section id="monthly-section">
    <div class="section-title">🏆 本月最值 <span class="badge" id="monthly-badge">TOP 30</span></div>
    <div class="card-grid" id="monthly-grid"></div>
  </section>
  <div class="last-updated" id="last-updated"></div>
</div>

<script>
// ==================== HEARTBEAT ====================
// 每 5 秒发一次心跳，告诉服务器 "我还活着"
const HEARTBEAT_INTERVAL = 5000;
let heartbeatTimer = null;

function startHeartbeat() {
  heartbeatTimer = setInterval(() => {
    fetch('/heartbeat', { cache: 'no-store' }).catch(() => {});
  }, HEARTBEAT_INTERVAL);
}

// 页面关闭时发送立即关闭信号
function sendShutdown() {
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/shutdown');
  } else {
    fetch('/shutdown', { method: 'POST', keepalive: true }).catch(() => {});
  }
}

window.addEventListener('beforeunload', sendShutdown);
window.addEventListener('pagehide', sendShutdown);
window.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') sendShutdown();
});

startHeartbeat();

// ==================== CONFIG ====================
const CACHE_KEY = 'steam_deals_cache';
const CACHE_TTL = 10 * 60 * 1000;
const MAX_ITEMS = 30;
const TODAY_HOURS = 24;

let currentSort = 'popularity';
let allDeals = [];
let todayDeals = [];

// ==================== INIT ====================
document.addEventListener('DOMContentLoaded', async () => {
  setupSortButtons();
  showSkeletons();
  const data = await loadDataWithCache();
  if (data) {
    allDeals = data;
    categorizeDeals();
    renderAll();
    document.getElementById('status-dot').style.background = 'var(--green)';
  }
});

function setupSortButtons() {
  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentSort = btn.dataset.sort;
      renderAll();
      document.querySelector('.container').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

// ==================== DATA LOADING ====================
async function loadDataWithCache() {
  try {
    const cached = JSON.parse(localStorage.getItem(CACHE_KEY));
    if (cached && cached.timestamp && (Date.now() - cached.timestamp < CACHE_TTL)) {
      console.log('📦 使用缓存 (' + Math.round((Date.now() - cached.timestamp) / 1000) + 's 前)');
      return cached.deals;
    }
  } catch(e) {}

  console.log('🌐 从 API 拉取数据...');
  try {
    const deals = await fetchAllDeals();
    localStorage.setItem(CACHE_KEY, JSON.stringify({ timestamp: Date.now(), deals }));
    return deals;
  } catch(e) {
    console.error('API 拉取失败:', e);
    try {
      const stale = JSON.parse(localStorage.getItem(CACHE_KEY));
      if (stale && stale.deals) {
        console.warn('⚠️ 使用过期缓存');
        showStaleBanner();
        return stale.deals;
      }
    } catch(e2) {}
    showError(e.message);
    return null;
  }
}

async function fetchAllDeals() {
  const PAGE_SIZE = 60;
  const TOTAL_PAGES = 6;
  const pageNumbers = Array.from({ length: TOTAL_PAGES }, (_, i) => i);
  const results = [];

  for (let i = 0; i < pageNumbers.length; i += 3) {
    const batch = pageNumbers.slice(i, i + 3);
    const batchResults = await Promise.allSettled(
      batch.map(p => fetchCheapSharkPage(p, PAGE_SIZE))
    );
    for (const r of batchResults) {
      if (r.status === 'fulfilled' && Array.isArray(r.value)) {
        results.push(...r.value);
      }
    }
  }

  let steamFeatured = [];
  try {
    steamFeatured = await fetchSteamFeatured();
  } catch(e) {
    console.warn('Steam featured API failed:', e);
  }

  const merged = mergeDeals(results, steamFeatured);
  const seen = new Set();
  const deduped = merged.filter(d => {
    const id = d.steamAppID || d.internalName;
    if (!id || seen.has(id)) return false;
    seen.add(id);
    return true;
  });

  console.log('✅ 共获取 ' + deduped.length + ' 个优惠 (CheapShark: ' + results.length + ', Steam: ' + steamFeatured.length + ')');

  // 用 Steam API 获取真实 CNY 价格
  console.log('💱 正在获取 Steam CNY 价格...');
  const withCNY = await enrichWithCNYPrices(deduped);
  const cnyCount = withCNY.filter(d => d.hasCNYPrice).length;
  console.log('💱 CNY 价格覆盖: ' + cnyCount + '/' + withCNY.length);
  return withCNY;
}

// ==================== STEAM CNY PRICE ENRICHMENT ====================
async function enrichWithCNYPrices(deals) {
  const appIds = [...new Set(
    deals.map(d => d.steamAppID).filter(id => id && id !== '0' && id !== 'undefined')
  )];

  if (appIds.length === 0) return deals;

  // 每批 15 个 app，最小化请求数
  const BATCH_SIZE = 15;
  const batches = [];
  for (let i = 0; i < appIds.length; i += BATCH_SIZE) {
    batches.push(appIds.slice(i, i + BATCH_SIZE));
  }

  // 分批并行请求（每次并发 4 批，避免触发频率限制）
  const priceMap = {};
  for (let i = 0; i < batches.length; i += 4) {
    const chunk = batches.slice(i, i + 4);
    const chunkResults = await Promise.allSettled(
      chunk.map(batch => fetchSteamCNYPrices(batch))
    );
    for (const r of chunkResults) {
      if (r.status === 'fulfilled') {
        Object.assign(priceMap, r.value);
      }
    }
  }

  // 获取汇率作为后备（始终获取，因为部分游戏可能没有 Steam 价格）
  const rate = await getUSDCNYRate();

  return deals.map(deal => {
    const appId = deal.steamAppID;
    if (appId && priceMap[appId]) {
      const sp = priceMap[appId];
      return {
        ...deal,
        salePriceCNY: sp.final / 100,
        normalPriceCNY: sp.initial / 100,
        discountPercentCNY: sp.discount_percent,
        hasCNYPrice: true,
        currency: 'CNY'
      };
    }
    // 后备：汇率换算
    const usdSale = parseFloat(deal.salePrice) || 0;
    const usdNormal = parseFloat(deal.normalPrice) || 0;
    return {
      ...deal,
      salePriceCNY: usdSale > 0 ? Math.round(usdSale * rate) : usdSale,
      normalPriceCNY: usdNormal > 0 ? Math.round(usdNormal * rate) : usdNormal,
      discountPercentCNY: parseFloat(deal.savings) || 0,
      hasCNYPrice: false,
      currency: 'CNY_EST'
    };
  });
}

async function fetchSteamCNYPrices(appIds) {
  try {
    const url = 'https://store.steampowered.com/api/appdetails?appids=' +
      appIds.join(',') + '&cc=cn&filters=price_overview';
    const resp = await fetch(url);
    if (!resp.ok) return {};
    const data = await resp.json();

    const priceMap = {};
    for (const [appId, info] of Object.entries(data)) {
      if (info && info.success && info.data && info.data.price_overview) {
        priceMap[appId] = info.data.price_overview;
      }
    }
    return priceMap;
  } catch(e) {
    return {};
  }
}

let _cachedRate = 7.25;
async function getUSDCNYRate() {
  try {
    const resp = await fetch('https://open.er-api.com/v6/latest/USD');
    if (resp.ok) {
      const data = await resp.json();
      _cachedRate = data.rates.CNY;
    }
  } catch(e) { /* 使用缓存汇率 */ }
  return _cachedRate;
}

async function fetchCheapSharkPage(pageNum, pageSize) {
  const url = 'https://www.cheapshark.com/api/1.0/deals?storeID=1&onSale=1&pageSize=' + pageSize + '&pageNumber=' + pageNum;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error('CheapShark API: HTTP ' + resp.status);
  const data = await resp.json();
  return data || [];
}

async function fetchSteamFeatured() {
  const url = 'https://store.steampowered.com/api/featuredcategories/?cc=cn';
  const resp = await fetch(url);
  if (!resp.ok) throw new Error('Steam API: HTTP ' + resp.status);
  const data = await resp.json();
  const result = [];

  const specials = data.specials || {};
  for (const item of (specials.items || [])) {
    result.push({
      steamAppID: String(item.id),
      title: item.name,
      salePrice: String(item.final_price / 100),
      normalPrice: String(item.original_price / 100),
      savings: String(item.discount_percent),
      steamRatingPercent: '0', steamRatingCount: '0', metacriticScore: '0',
      thumb: item.header_image || item.large_capsule_image || '',
      dealRating: '9.0', releaseDate: 0,
      lastChange: Math.floor(Date.now() / 1000),
      discountExpiration: item.discount_expiration || null,
      isSteamFeatured: true, isDailyDeal: false
    });
  }

  const daily = data.cat_dailydeal || {};
  for (const item of (daily.items || [])) {
    if (!item.id) continue;
    result.push({
      steamAppID: String(item.id),
      title: item.name,
      salePrice: String(item.final_price / 100),
      normalPrice: String(item.original_price / 100),
      savings: String(item.discount_percent),
      steamRatingPercent: '0', steamRatingCount: '0', metacriticScore: '0',
      thumb: item.header_image || '',
      dealRating: '9.5', releaseDate: 0,
      lastChange: Math.floor(Date.now() / 1000),
      discountExpiration: null,
      isSteamFeatured: true, isDailyDeal: true
    });
  }

  return result;
}

function mergeDeals(cheapSharkDeals, steamFeatured) {
  const steamMap = new Map();
  for (const sf of steamFeatured) steamMap.set(sf.steamAppID, sf);

  const enriched = cheapSharkDeals.map(d => {
    const sf = steamMap.get(d.steamAppID);
    if (sf) {
      steamMap.delete(d.steamAppID);
      return { ...d, isSteamFeatured: true, discountExpiration: sf.discountExpiration, isDailyDeal: sf.isDailyDeal };
    }
    return d;
  });

  return [...steamMap.values(), ...enriched];
}

// ==================== CATEGORIZATION ====================
function categorizeDeals() {
  const now = Math.floor(Date.now() / 1000);
  const todayThreshold = now - (TODAY_HOURS * 3600);

  todayDeals = allDeals.filter(d => {
    if (d.isDailyDeal) return true;
    if (d.lastChange && parseInt(d.lastChange) > todayThreshold) return true;
    if (d.discountExpiration && parseInt(d.discountExpiration) - now < 172800) return true;
    return false;
  });
}

// ==================== SORT ====================
function getSortKey(deal, sort) {
  switch (sort) {
    case 'popularity': {
      const count = parseInt(deal.steamRatingCount) || 0;
      const dRating = parseFloat(deal.dealRating) || 0;
      return count * 10 + dRating;
    }
    case 'rating': {
      const meta = parseFloat(deal.metacriticScore) || 0;
      const steamPct = parseFloat(deal.steamRatingPercent) || 0;
      const count = parseInt(deal.steamRatingCount) || 0;
      return meta * 0.6 + steamPct * 0.4 + Math.min(count / 1000, 1) * 10;
    }
    case 'price': {
      // 用 ?? 等价逻辑处理价格，避免 0（免费游戏）被 || 误判为无效值
      const rawPrice = deal.hasCNYPrice ? deal.salePriceCNY : (parseFloat(deal.salePrice) * 7.25);
      const price = (rawPrice === 0 || rawPrice > 0) ? rawPrice : 999;
      const meta = parseFloat(deal.metacriticScore) || 0;
      const steamPct = parseFloat(deal.steamRatingPercent) || 0;
      const savings = deal.hasCNYPrice ? (deal.discountPercentCNY || 0) : (parseFloat(deal.savings) || 0);
      // 100% 免费游戏额外加分
      const freeBonus = (savings >= 100 || rawPrice === 0) ? 15 : 0;
      const quality = meta * 0.4 + steamPct * 0.4 + savings * 0.2 + freeBonus;
      return quality / (price + 0.01);
    }
    default: return 0;
  }
}

function sortDeals(deals, sort) {
  return [...deals].sort((a, b) => getSortKey(b, sort) - getSortKey(a, sort));
}

// ==================== RENDER ====================
function renderAll() {
  const todaySorted = sortDeals(todayDeals, currentSort).slice(0, MAX_ITEMS);
  renderCards('today-grid', todaySorted, true);
  const monthlySorted = sortDeals(allDeals, currentSort).slice(0, MAX_ITEMS);
  renderCards('monthly-grid', monthlySorted, true);

  document.getElementById('today-badge').textContent = todaySorted.length + ' 款';
  document.getElementById('monthly-badge').textContent = 'TOP ' + monthlySorted.length;

  const now = new Date();
  document.getElementById('last-updated').textContent =
    '最后更新: ' + now.toLocaleString('zh-CN') + ' · 数据来源: Steam / CheapShark · CNY';
}

function renderCards(gridId, deals, showRank) {
  const grid = document.getElementById(gridId);
  if (!deals || deals.length === 0) {
    grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-dim)">暂无数据</div>';
    return;
  }

  grid.setAttribute('data-ranked', showRank ? 'true' : 'false');
  grid.innerHTML = deals.map((d, i) => renderCard(d, i, showRank)).join('');

  requestAnimationFrame(() => {
    grid.querySelectorAll('img[data-src]').forEach(img => {
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
    });
  });
}

function renderCard(deal, index, showRank) {
  const title = escapeHTML(deal.title || 'Unknown');
  const steamAppID = deal.steamAppID || '';
  const storeURL = steamAppID
    ? 'https://store.steampowered.com/app/' + steamAppID + '/?cc=cn'
    : 'https://store.steampowered.com/search/?term=' + encodeURIComponent(title);

  // 使用 ?? 正确处理 0 值（免费游戏价格=0 是合法的）
  const salePrice = deal.salePriceCNY ?? (parseFloat(deal.salePrice) * 7.25);
  const normalPrice = deal.normalPriceCNY ?? (parseFloat(deal.normalPrice) * 7.25);
  const savings = deal.hasCNYPrice ? (deal.discountPercentCNY ?? 0) : (parseFloat(deal.savings) || 0);
  const isFree = (salePrice === 0 || salePrice < 0.05) && normalPrice > 0;
  const is100Off = savings >= 99; // 100% off / 限时免费
  const isEstimated = !deal.hasCNYPrice;

  let priceHTML = '';
  if (isFree && normalPrice > 0) {
    priceHTML = '<span class="price-original">' + (isEstimated ? '~' : '') + '¥' + normalPrice.toFixed(0) + '</span><span class="price-sale" style="color:var(--green)">免费!</span>';
  } else if (salePrice > 0) {
    priceHTML =
      (normalPrice > salePrice ? '<span class="price-original">' + (isEstimated ? '~' : '') + '¥' + normalPrice.toFixed(0) + '</span>' : '') +
      '<span class="price-sale">' + (isEstimated ? '~' : '') + '¥' + salePrice.toFixed(2) + '</span>';
  } else if (isFree) {
    priceHTML = '<span class="price-sale" style="color:var(--green)">免费</span>';
  } else {
    priceHTML = '<span class="price-sale">' + (isEstimated ? '~' : '') + '¥' + (normalPrice.toFixed(0) || '—') + '</span>';
  }

  // 折扣标签：100% off 用特殊样式
  let discountHTML = '';
  if (is100Off) {
    discountHTML = '<span class="discount-badge" style="background:#e55;color:#fff;animation:pulse-badge 1.5s ease-in-out infinite">限免!</span>';
  } else if (savings >= 80) {
    discountHTML = '<span class="discount-badge medium">-' + Math.round(savings) + '%</span>';
  } else if (savings > 0) {
    discountHTML = '<span class="discount-badge">-' + Math.round(savings) + '%</span>';
  }

  const dealRating = parseFloat(deal.dealRating) || 0;
  let dealRatingHTML = '';
  if (dealRating >= 9) {
    dealRatingHTML = '<span class="deal-badge">🏅 ' + dealRating.toFixed(1) + '</span>';
  }

  const metacritic = parseFloat(deal.metacriticScore) || 0;
  const steamPct = parseFloat(deal.steamRatingPercent) || 0;
  const steamCount = parseInt(deal.steamRatingCount) || 0;

  let ratingHTML = '';
  if (metacritic > 0 || steamPct > 0) {
    const parts = [];
    if (metacritic > 0) {
      let cls = 'meta-high';
      if (metacritic < 60) cls = 'meta-low';
      else if (metacritic < 75) cls = 'meta-mid';
      parts.push('<span title="Metacritic">📊 <span class="rating-score ' + cls + '">' + metacritic + '</span></span>');
    }
    if (steamPct > 0) {
      parts.push('<span title="Steam 好评率">👍 <span class="rating-score">' + steamPct + '%</span></span>');
    }
    if (steamCount > 0) {
      parts.push('<span class="review-count">' + formatCount(steamCount) + ' 评</span>');
    }
    ratingHTML = parts.join('');
  }

  let featuredTag = '';
  let cardExtraStyle = '';
  if (is100Off) {
    featuredTag = '<span style="position:absolute;top:8px;left:8px;background:linear-gradient(135deg,#e55,#ff3377);color:#fff;font-size:0.7rem;font-weight:700;padding:3px 8px;border-radius:4px;z-index:2;box-shadow:0 0 12px rgba(255,51,119,0.5)">🎁 限时免费</span>';
    cardExtraStyle = 'border:2px solid rgba(255,51,119,0.4);box-shadow:0 0 16px rgba(255,51,119,0.12);';
  } else if (deal.isDailyDeal) {
    featuredTag = '<span style="position:absolute;top:8px;left:8px;background:var(--red);color:#fff;font-size:0.62rem;padding:2px 6px;border-radius:4px;z-index:2">每日特惠</span>';
  } else if (deal.isSteamFeatured) {
    featuredTag = '<span style="position:absolute;top:8px;left:8px;background:var(--accent);color:#fff;font-size:0.62rem;padding:2px 6px;border-radius:4px;z-index:2">官方推荐</span>';
  }

  const thumb = deal.thumb || 'https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/' + steamAppID + '/capsule_231x87.jpg';

  let releaseHTML = '';
  if (deal.releaseDate && parseInt(deal.releaseDate) > 0) {
    const d = new Date(parseInt(deal.releaseDate) * 1000);
    releaseHTML = '<div class="release-date">📅 ' + d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '</div>';
  }

  const rankHTML = showRank && index < 3
    ? '<span class="rank-num">#' + (index + 1) + '</span>'
    : '';

  return (
    '<a href="' + storeURL + '" target="_blank" rel="noopener" class="card" title="' + title + '"' +
    (cardExtraStyle ? ' style="' + cardExtraStyle + '"' : '') + '>' +
      '<div class="card-img-wrap">' +
        '<img data-src="' + thumb.replace('http:', 'https:') + '"' +
        ' src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOcAAABXAQMAAABLx9IFAAAAA1BMVEX/AAAZuKKeAAAAFklEQVQ4y2P4z8BQz0BKYBw1YNSAUQMAMwIC/77rm2AAAAAASUVORK5CYII="' +
        ' alt="' + title + '">' +
        discountHTML + dealRatingHTML + featuredTag + rankHTML +
      '</div>' +
      '<div class="card-body">' +
        '<div class="card-title">' + title + '</div>' +
        (isEstimated ? '<div style="font-size:0.6rem;color:var(--orange);margin-bottom:2px">⚠ 估算价格 (USD换算)</div>' : '') +
        '<div class="card-pricing">' + priceHTML + '</div>' +
        '<div class="card-ratings">' + ratingHTML + '</div>' +
        releaseHTML +
      '</div>' +
    '</a>'
  );
}

function showSkeletons() {
  [document.getElementById('today-grid'), document.getElementById('monthly-grid')].forEach(grid => {
    grid.innerHTML = Array.from({ length: 12 }, () =>
      '<div class="skeleton-card"><div class="skeleton-img"></div><div class="skeleton-body"><div class="skeleton-line"></div><div class="skeleton-line price"></div><div class="skeleton-line short"></div></div></div>'
    ).join('');
  });
}

function showError(msg) {
  const errHTML = '<div class="error-msg">⚠️ 数据加载失败: ' + escapeHTML(msg) + '<br><button onclick="location.reload()">🔄 重新加载</button></div>';
  document.getElementById('today-grid').innerHTML = errHTML;
  document.getElementById('monthly-grid').innerHTML = errHTML;
  document.getElementById('status-dot').style.background = 'var(--red)';
}

function showStaleBanner() {
  const banner = document.createElement('div');
  banner.style.cssText = 'text-align:center;padding:12px;background:rgba(255,170,51,0.1);color:var(--orange);font-size:0.85rem;margin-bottom:16px;border-radius:8px;';
  banner.textContent = '⚠️ 无法连接 API，当前显示缓存数据，可能已过时';
  const app = document.getElementById('app');
  app.insertBefore(banner, app.firstChild);
}

function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatCount(n) {
  if (n >= 100000) return (n / 10000).toFixed(1) + '万';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return String(n);
}
</script>

</body>
</html>'''


# ============================================================
# HTTP 服务器
# ============================================================
_last_heartbeat = time.time()
_shutdown_requested = False
_lock = threading.Lock()


class Handler(http.server.BaseHTTPRequestHandler):
    """自定义请求处理器"""

    def log_message(self, format, *args):
        """ suppress noisy logs """
        pass

    def _send(self, content, content_type='text/plain; charset=utf-8', status=200):
        body = content.encode('utf-8') if isinstance(content, str) else content
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        global _last_heartbeat

        if self.path in ('/', '/steam-deals.html'):
            # 主页
            self._send(HTML_PAGE, 'text/html; charset=utf-8')

        elif self.path == '/heartbeat':
            # 心跳 — 浏览器还开着
            with _lock:
                _last_heartbeat = time.time()
            self._send('ok')

        elif self.path == '/shutdown':
            # 浏览器主动请求关闭
            self._set_shutdown()
            self._send('bye')

        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/shutdown':
            self._set_shutdown()
            self._send('bye')
        else:
            self.send_error(404)

    def _set_shutdown(self):
        global _shutdown_requested
        with _lock:
            _shutdown_requested = True


def watchdog(httpd, timeout=20):
    """看门狗线程：超过 timeout 秒没收到心跳就关闭服务器"""
    global _last_heartbeat, _shutdown_requested

    while True:
        time.sleep(3)

        with _lock:
            idle = time.time() - _last_heartbeat
            should_stop = _shutdown_requested or idle > timeout

        if should_stop:
            print(f'\n🛑 {"收到关闭信号" if _shutdown_requested else "心跳超时(" + str(int(idle)) + "s)"}，正在停止服务器...')
            httpd.shutdown()
            return


def main():
    global _last_heartbeat

    port = 8765
    # 自动找可用端口
    for attempt in range(20):
        try:
            server = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
            break
        except OSError:
            port += 1
    else:
        print('❌ 无法找到可用端口')
        input('按回车退出...')
        return

    server.timeout = 1  # 允许 shutdown() 快速生效

    # 启动看门狗
    watch = threading.Thread(target=watchdog, args=(server, 20), daemon=True)
    watch.start()

    # 记录初始心跳时间
    _last_heartbeat = time.time()

    # 打开浏览器
    url = f'http://localhost:{port}'
    print(f'🚀 正在打开 {url}')
    webbrowser.open(url)

    print('━' * 50)
    print('  🎮 Steam 优惠精选 已启动')
    print(f'  地址: {url}')
    print('  关闭浏览器页面即可自动退出')
    print('  或者按 Ctrl+C 手动退出')
    print('━' * 50)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n⏹️ 用户中断')

    server.server_close()
    print('✅ 服务器已停止，程序退出')


if __name__ == '__main__':
    main()
