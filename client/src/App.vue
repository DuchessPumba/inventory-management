<template>
  <div class="app" :class="shellClass">
    <Sidebar
      :open="sidebarOpen"
      @show-profile-details="openProfileDetails"
      @show-tasks="openTasks"
      @toggle-collapse="onToggleCollapse"
    />
    <!-- Backdrop for the phone drawer and the tablet overlay; never on desktop -->
    <div v-if="sidebarOpen && mode !== 'desktop'" class="sidebar-backdrop" @click="closeSidebar"></div>

    <div class="app-main">
      <!-- Slim top bar, only shown below 768px where the sidebar is a drawer -->
      <div class="mobile-bar">
        <button
          ref="menuButton"
          class="menu-button"
          type="button"
          :aria-label="t('nav.menu')"
          aria-controls="app-sidebar"
          :aria-expanded="sidebarOpen ? 'true' : 'false'"
          @click="sidebarOpen = !sidebarOpen"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true">
            <path d="M4 7h16M4 12h16M4 17h16" />
          </svg>
        </button>
        <span class="mobile-bar-title">{{ t('nav.companyName') }}</span>
      </div>
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import { useSidebar } from './composables/useSidebar'
import FilterBar from './components/FilterBar.vue'
import Sidebar from './components/Sidebar.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    Sidebar,
    ProfileDetailsModal,
    TasksModal
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Drawer (phones) / overlay (tablets) open state; unused on desktop
    const route = useRoute()
    const { mode, collapsed: collapsedState, toggle: toggleCollapsed } = useSidebar()
    const sidebarOpen = ref(false)
    const menuButton = ref(null)
    const closeSidebar = () => {
      sidebarOpen.value = false
    }
    watch(() => route.path, closeSidebar)
    // Any viewport mode change resets it, so resizing never reopens a stale drawer/overlay
    watch(mode, closeSidebar)

    // One class on the shell drives --shell-sidebar-width, shared by the sidebar width
    // and the main column margin (see styles below).
    const shellClass = computed(() => ({
      'app--mobile': mode.value === 'mobile',
      'app--tablet': mode.value === 'tablet',
      'app--collapsed': mode.value === 'desktop' && collapsedState.value
    }))

    // Desktop: collapse/expand the rail (persisted). Tablet: open/close the overlay.
    const onToggleCollapse = () => {
      if (mode.value === 'desktop') toggleCollapsed()
      else sidebarOpen.value = !sidebarOpen.value
    }

    // Modals open above the sidebar, so the drawer/overlay and backdrop must close first
    const openProfileDetails = () => {
      closeSidebar()
      showProfileDetails.value = true
    }
    const openTasks = () => {
      closeSidebar()
      showTasks.value = true
    }

    const onKeydown = (e) => {
      if (e.key === 'Escape' && sidebarOpen.value) {
        closeSidebar()
        // Return focus to whichever control opened it: menu button (phone) or rail toggle (tablet)
        const trigger = mode.value === 'mobile'
          ? menuButton.value
          : document.querySelector('#app-sidebar .sidebar-toggle')
        if (trigger) trigger.focus()
      }
    }
    onMounted(() => document.addEventListener('keydown', onKeydown))
    onUnmounted(() => document.removeEventListener('keydown', onKeydown))

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      sidebarOpen,
      menuButton,
      mode,
      shellClass,
      closeSidebar,
      openProfileDetails,
      openTasks,
      onToggleCollapse,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>


<style>
:root {
  /* spacing (4px base) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;

  /* shape */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-full: 999px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-lg: 0 10px 30px rgba(15, 23, 42, 0.12);

  /* layout */
  --sidebar-width: 240px;
  --sidebar-width-collapsed: 72px;
  --content-max: 1280px;
  /* Height of the phone top bar; 0 from 768px up. The filter toolbar sticks below it. */
  --topbar-height: 0px;

  /* color */
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-hover: #f1f5f9;
  --border: #e2e8f0;
  --text: #0f172a;
  --text-muted: #64748b;
  --text-subtle: #94a3b8;
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --accent-soft: #eff6ff;
  --success: #059669;
  --warning: #ca8a04;
  --danger: #dc2626;
  --info: #2563eb;

  /* type */
  --text-xs: 12px;
  --text-sm: 14px;
  --text-base: 16px;
  --text-lg: 20px;
  --text-xl: 24px;
  --text-2xl: 32px;

  /* Modals use 2000 and the profile/language dropdowns live inside the sidebar's
     stacking context, so modals always sit above the sidebar and toolbar. */
  --z-sidebar: 100;
  --z-toolbar: 90;
}

@media (max-width: 767.98px) {
  :root {
    --topbar-height: 56px;
  }
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: var(--text-sm);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ---------- App shell ---------- */

.app {
  min-height: 100vh;
  /* Single source of truth for the sidebar width and the main column's left margin */
  --shell-sidebar-width: var(--sidebar-width);
}

.app--collapsed,
.app--tablet {
  --shell-sidebar-width: var(--sidebar-width-collapsed);
}

/* min-width: 0 stops wide tables and flex children from pushing the page sideways.
   On tablets the margin is the rail width even while the sidebar is expanded: the
   expanded sidebar is an overlay, so the content does not shift. */
.app-main {
  margin-left: var(--shell-sidebar-width);
  transition: margin-left 0.2s ease;
  min-width: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-8);
}

.mobile-bar,
.sidebar-backdrop {
  display: none;
}

@media (prefers-reduced-motion: reduce) {
  .app-main {
    transition: none;
  }
}

@media (max-width: 1023.98px) {
  /* One step below the sidebar so the drawer/overlay is above it */
  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.4);
    z-index: calc(var(--z-sidebar) - 1);
  }
}

@media (max-width: 767.98px) {
  .app-main {
    margin-left: 0;
  }

  .mobile-bar {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    height: var(--topbar-height);
    padding: 0 var(--space-4);
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: var(--z-toolbar);
  }
}

.menu-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.menu-button:hover {
  background: var(--surface-hover);
}

.menu-button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.mobile-bar-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 767.98px) {
  .main-content {
    padding: var(--space-4);
  }
}

/* ---------- Page header ---------- */

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: 600;
  line-height: 1.25;
  color: var(--text);
  margin-bottom: var(--space-1);
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-sm);
}

/* ---------- Stat cards ---------- */

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--surface);
  padding: var(--space-4) var(--space-6);
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
}

.stat-label {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.25;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value {
  color: var(--warning);
}

.stat-card.success .stat-value {
  color: var(--success);
}

.stat-card.danger .stat-value {
  color: var(--danger);
}

.stat-card.info .stat-value {
  color: var(--info);
}

/* ---------- Cards ---------- */

/* margin-bottom is relied on by views to space stacked cards */
.card {
  background: var(--surface);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-6);
}

@media (max-width: 767.98px) {
  .card {
    padding: var(--space-4);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 600;
  line-height: 1.25;
  color: var(--text);
}

/* ---------- Tables ---------- */

/* Tables scroll inside their own container, never the page */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--bg);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-weight: 500;
  color: var(--text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--surface-hover);
  color: var(--text);
  font-size: var(--text-sm);
  font-variant-numeric: tabular-nums;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--surface-hover);
}

/* ---------- Badges ---------- */

.badge {
  display: inline-block;
  padding: var(--space-1) 10px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
  line-height: 1.25;
  white-space: nowrap;
}

.badge.success {
  background: #d1fae5;
  color: #065f46;
}

.badge.warning {
  background: #fed7aa;
  color: #92400e;
}

.badge.danger {
  background: #fecaca;
  color: #991b1b;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.badge.increasing {
  background: #d1fae5;
  color: #065f46;
}

.badge.decreasing {
  background: #fecaca;
  color: #991b1b;
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.high {
  background: #fecaca;
  color: #991b1b;
}

.badge.medium {
  background: #fed7aa;
  color: #92400e;
}

.badge.low {
  background: #dbeafe;
  color: #1e40af;
}

/* ---------- Loading and error ---------- */

.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-sm);
  margin: var(--space-4) 0;
  font-size: var(--text-sm);
}

/* ---------- Buttons ---------- */

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.btn-primary {
  background: var(--accent);
  color: #ffffff;
}

.btn.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn.btn-primary:active:not(:disabled) {
  background: #1e40af;
}

.btn.btn-secondary {
  background: var(--surface);
  border-color: var(--border);
  color: var(--text);
}

.btn.btn-secondary:hover:not(:disabled) {
  background: var(--surface-hover);
}

.btn.btn-secondary:active:not(:disabled) {
  background: var(--border);
}

.btn.btn-ghost {
  background: transparent;
  color: var(--text-muted);
}

.btn.btn-ghost:hover:not(:disabled) {
  background: var(--surface-hover);
  color: var(--text);
}

.btn.btn-ghost:active:not(:disabled) {
  background: var(--border);
}
</style>
