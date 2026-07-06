import { reactive, computed } from 'vue'

const STATS_KEY = 'vd_download_stats'

function defaultStats() {
  const today = new Date().toISOString().slice(0, 10)
  return { today: { [today]: {} }, total: {} }
}

function loadStats() {
  try {
    const raw = localStorage.getItem(STATS_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      return ensureTodayEntry(parsed)
    }
  } catch { /* noop */ }
  return defaultStats()
}

function saveStats(v) {
  try { localStorage.setItem(STATS_KEY, JSON.stringify(v)) } catch { /* noop */ }
}

function ensureTodayEntry(stats) {
  const today = new Date().toISOString().slice(0, 10)
  if (!stats.today[today]) stats.today[today] = {}
  return stats
}

export function useStats() {
  const stats = reactive(loadStats())

  function recordDownload(platform, bytes) {
    const today = new Date().toISOString().slice(0, 10)
    if (!stats.today[today]) stats.today[today] = {}
    if (!stats.today[today][platform]) stats.today[today][platform] = { count: 0, bytes: 0 }
    stats.today[today][platform].count += 1
    stats.today[today][platform].bytes += bytes
    if (!stats.total[platform]) stats.total[platform] = { count: 0, bytes: 0 }
    stats.total[platform].count += 1
    stats.total[platform].bytes += bytes
    saveStats(stats)
  }

  const today = computed(() => {
    const todayStr = new Date().toISOString().slice(0, 10)
    const day = stats.today[todayStr] || {}
    const r = {}
    let c = 0, b = 0
    for (const [p, d] of Object.entries(day)) {
      r[p] = { count: d.count, bytes: d.bytes }
      c += d.count
      b += d.bytes
    }
    r.total = { count: c, bytes: b }
    return r
  })

  const total = computed(() => {
    const r = {}
    let c = 0, b = 0
    for (const [p, d] of Object.entries(stats.total)) {
      r[p] = { count: d.count, bytes: d.bytes }
      c += d.count
      b += d.bytes
    }
    r.total = { count: c, bytes: b }
    return r
  })

  function getStats() {
    return { today: today.value, total: total.value }
  }

  return { stats, recordDownload, getStats, todayTotal: today, grandTotal: total }
}
