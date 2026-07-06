<template>
  <div class="stats-panel">
    <div class="stats-section">
      <div class="stats-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
        今日下载
      </div>
      <div class="stats-rows">
        <div v-for="p in platformKeys(todayTotal)" :key="p" class="stats-row">
          <span class="stats-label">{{ platformNames[p] || p }}</span>
          <span class="stats-value">{{ todayTotal[p].count }} 个</span>
          <span class="stats-divider">|</span>
          <span class="stats-bytes">{{ formatSize(todayTotal[p].bytes) }}</span>
        </div>
        <div class="stats-divider-row"></div>
        <div class="stats-row stats-summary">
          <span class="stats-label">合计</span>
          <span class="stats-value">{{ todayTotal.total.count }} 个</span>
          <span class="stats-divider">|</span>
          <span class="stats-bytes">{{ formatSize(todayTotal.total.bytes) }}</span>
        </div>
      </div>
    </div>

    <div class="stats-separator"></div>

    <div class="stats-section">
      <div class="stats-title stats-title-total">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 20V10" />
          <path d="M18 20V4" />
          <path d="M6 20v-4" />
        </svg>
        总下载
      </div>
      <div class="stats-rows">
        <div v-for="p in platformKeys(grandTotal)" :key="p" class="stats-row">
          <span class="stats-label">{{ platformNames[p] || p }}</span>
          <span class="stats-value">{{ grandTotal[p].count }} 个</span>
          <span class="stats-divider">|</span>
          <span class="stats-bytes">{{ formatSize(grandTotal[p].bytes) }}</span>
        </div>
        <div class="stats-divider-row"></div>
        <div class="stats-row stats-summary">
          <span class="stats-label">合计</span>
          <span class="stats-value">{{ grandTotal.total.count }} 个</span>
          <span class="stats-divider">|</span>
          <span class="stats-bytes">{{ formatSize(grandTotal.total.bytes) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, unref } from 'vue'

const props = defineProps({
  stats: { type: Object, required: true }
})

const platformNames = { bilibili: 'B站', douyin: '抖音' }
const platformOrder = ['bilibili', 'douyin']

const todayTotal = computed(() => unref(props.stats.todayTotal))
const grandTotal = computed(() => unref(props.stats.grandTotal))

function platformKeys(data) {
  return platformOrder.filter(p => data[p])
}

function formatSize(bytes) {
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${i === 0 ? size : Math.round(size)} ${units[i]}`
}
</script>

<style scoped>
.stats-panel {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 16px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.stats-title {
  font-size: 12px;
  font-weight: var(--font-weight-semibold);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.stats-title svg {
  opacity: 0.6;
}

.stats-title-total {
  margin-top: 0;
}

.stats-rows {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stats-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-primary);
  line-height: 1.6;
}

.stats-label {
  min-width: 28px;
  color: var(--text-muted);
}

.stats-value {
  font-family: var(--font-mono);
  font-weight: var(--font-weight-medium);
  min-width: 50px;
}

.stats-divider {
  color: var(--text-dim);
  user-select: none;
}

.stats-bytes {
  font-family: var(--font-mono);
  color: var(--text-secondary);
}

.stats-divider-row {
  height: 1px;
  background: var(--border);
  margin: 4px 0 3px;
}

.stats-summary .stats-label {
  color: var(--text-secondary);
  font-weight: var(--font-weight-semibold);
}

.stats-summary .stats-value,
.stats-summary .stats-bytes {
  color: var(--accent);
}

.stats-separator {
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    var(--border) 15%,
    var(--border) 85%,
    transparent
  );
  margin: 14px 0;
}
</style>
