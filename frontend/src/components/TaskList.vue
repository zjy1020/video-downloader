<template>
  <div class="task-list-panel">
    <div class="panel-header">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
      下载任务
      <span class="task-count">{{ filteredTasks.length }}</span>
      <div class="header-spacer"></div>
      <button v-if="hasFinished" class="btn-clear" @click="clearFinished">清空已结束</button>
      <button v-if="props.tasks.length > 0" class="btn-clear btn-clear-all" @click="clearAll">清空全部</button>
    </div>

    <div class="filter-tabs" v-if="tasks.length > 0">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="filter-tab"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <Transition name="fade" mode="out-in">
      <div v-if="filteredTasks.length === 0" class="empty-state" :key="'empty'">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="empty-ico">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        <div class="empty-text">暂无下载任务</div>
        <div class="empty-hint">解析链接后点击下载添加任务</div>
      </div>

      <div v-else class="task-scroll" :key="'list'">
        <TransitionGroup name="list">
          <TaskCard
            v-for="task in filteredTasks"
            :key="task.task_id"
            :task="task"
            @retry="(id) => emit('retry', id)"
            @delete="(id) => emit('delete', id)"
          />
        </TransitionGroup>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import TaskCard from './TaskCard.vue'

const props = defineProps({
  tasks: { type: Array, default: () => [] },
})

const emit = defineEmits(['retry', 'delete'])
const API_BASE = '/api'

const activeTab = ref('all')

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'active', label: '进行中' },
  { key: 'done', label: '已完成' },
  { key: 'failed', label: '失败' },
]

const hasFinished = computed(() =>
  props.tasks.some((t) => t.status === 'success' || t.status === 'failed')
)

async function clearFinished() {
  try {
    await axios.delete(`${API_BASE}/tasks?scope=finished`)
    emit('delete', '__all__')
  } catch { /* noop */ }
}

async function clearAll() {
  try {
    await axios.delete(`${API_BASE}/tasks?scope=all`)
    emit('delete', '__all__')
  } catch { /* noop */ }
}

const filteredTasks = computed(() => {
  if (activeTab.value === 'all') return props.tasks
  if (activeTab.value === 'active') return props.tasks.filter(t => t.status === 'waiting' || t.status === 'downloading')
  if (activeTab.value === 'done') return props.tasks.filter(t => t.status === 'success')
  if (activeTab.value === 'failed') return props.tasks.filter(t => t.status === 'failed')
  return props.tasks
})
</script>

<style scoped>
.task-list-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.panel-header {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.task-count {
  background: var(--accent);
  color: #fff;
  font-size: 10px;
  padding: 1px 7px;
  border-radius: 8px;
  font-weight: 600;
}

.header-spacer { flex: 1; }

.btn-clear {
  padding: 3px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-clear:hover {
  color: var(--error);
  border-color: rgba(248, 113, 113, 0.3);
  background: var(--error-bg);
}

.filter-tabs {
  display: flex;
  gap: 2px;
  padding: 10px 0 8px;
  flex-shrink: 0;
  background: var(--bg-surface);
  position: sticky;
  top: 0;
  z-index: 2;
}

.filter-tab {
  flex: 1;
  padding: 5px 0;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s;
}

.filter-tab:hover {
  color: var(--text-secondary);
  background: var(--bg-hover);
}

.filter-tab.active {
  color: var(--accent);
  background: var(--accent-glow);
}

.task-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 2px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  gap: 6px;
}

.empty-ico { opacity: 0.3; }

.empty-text {
  font-size: 14px;
  font-weight: 500;
}

.empty-hint {
  font-size: 12px;
  opacity: 0.7;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.list-enter-active {
  transition: all 0.25s ease-out;
}
.list-leave-active {
  transition: all 0.15s ease-in;
}
.list-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.list-leave-to {
  opacity: 0;
  transform: translateX(10px);
}
.list-move {
  transition: transform 0.2s ease;
}
</style>
