<template>
  <aside
    id="app-sidebar"
    class="sidebar"
    :class="{
      'sidebar-open': open,
      'sidebar-mobile': mode === 'mobile',
      'sidebar-overlay': mode === 'tablet' && open,
      'is-rail': isRail
    }"
  >
    <div class="sidebar-brand">
      <!-- Rail: decorative initial only; the full name stays readable via the sr-only text below -->
      <div v-if="isRail" class="brand-mark" aria-hidden="true">{{ brandInitial }}</div>
      <div class="brand-name" :class="{ 'sr-only': isRail }" :title="t('nav.companyName')">{{ t('nav.companyName') }}</div>
      <div class="brand-subtitle" :class="{ 'sr-only': isRail }" :title="t('nav.subtitle')">{{ t('nav.subtitle') }}</div>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :class="{ active: $route.path === item.to }"
        :title="t(item.label)"
        :aria-label="t(item.label)"
      >
        <svg
          class="nav-icon"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path v-for="d in item.icon" :key="d" :d="d" />
        </svg>
        <span class="nav-label">{{ t(item.label) }}</span>
      </router-link>
    </nav>

    <!-- Hidden on phones: the top-bar menu button in App.vue handles the drawer there -->
    <div v-if="mode !== 'mobile'" class="sidebar-toggle-row">
      <button
        class="nav-item sidebar-toggle"
        type="button"
        :title="toggleLabel"
        :aria-label="toggleLabel"
        aria-controls="app-sidebar"
        :aria-expanded="isRail ? 'false' : 'true'"
        @click="$emit('toggle-collapse')"
      >
        <svg
          class="nav-icon"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path v-for="d in toggleIcon" :key="d" :d="d" />
        </svg>
        <span class="nav-label">{{ toggleLabel }}</span>
      </button>
    </div>

    <div class="sidebar-footer">
      <LanguageSwitcher :compact="isRail" />
      <ProfileMenu
        :compact="isRail"
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </aside>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

export default {
  name: 'Sidebar',
  components: { LanguageSwitcher, ProfileMenu },
  props: {
    // Below 768px: drawer is open. 768-1023px: the full sidebar is expanded as an overlay.
    // Ignored on desktop, where the collapsed preference decides.
    open: {
      type: Boolean,
      default: false
    }
  },
  emits: ['show-profile-details', 'show-tasks', 'toggle-collapse'],
  setup(props) {
    const { t } = useI18n()
    const { collapsed, mode } = useSidebar()

    // Rail (icons only) when: desktop and collapsed, or tablet and the overlay is not open.
    // On phones the drawer always shows full labels, so the collapsed preference is ignored.
    const isRail = computed(() => {
      if (mode.value === 'desktop') return collapsed.value
      if (mode.value === 'tablet') return !props.open
      return false
    })

    const brandInitial = computed(() => Array.from(t('nav.companyName'))[0] || '')
    const toggleLabel = computed(() => (isRail.value ? t('nav.expand') : t('nav.collapse')))
    // chevrons-right when collapsed, chevrons-left when expanded
    const toggleIcon = computed(() =>
      isRail.value
        ? ['M13 17l5-5-5-5', 'M6 17l5-5-5-5']
        : ['M11 17l-5-5 5-5', 'M18 17l-5-5 5-5']
    )

    // Same order and i18n keys as the former top nav
    const navItems = [
      { to: '/', label: 'nav.overview', icon: ['M4 4h7v7H4z', 'M13 4h7v7h-7z', 'M4 13h7v7H4z', 'M13 13h7v7h-7z'] },
      { to: '/inventory', label: 'nav.inventory', icon: ['M3 7l9-4 9 4v10l-9 4-9-4z', 'M3 7l9 4 9-4', 'M12 11v10'] },
      { to: '/orders', label: 'nav.orders', icon: ['M9 4h6v3H9z', 'M9 5.5H7a1 1 0 00-1 1V20a1 1 0 001 1h10a1 1 0 001-1V6.5a1 1 0 00-1-1h-2', 'M9 12h6', 'M9 16h4'] },
      { to: '/spending', label: 'nav.finance', icon: ['M12 3a9 9 0 100 18 9 9 0 000-18z', 'M14.5 9.5c-.5-1-1.4-1.5-2.5-1.5-1.4 0-2.5.8-2.5 2s1 1.7 2.5 2 2.5.8 2.5 2-1.1 2-2.5 2c-1.1 0-2-.5-2.5-1.5', 'M12 6.5v1.5', 'M12 16v1.5'] },
      { to: '/demand', label: 'nav.demandForecast', icon: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'] },
      { to: '/restocking', label: 'nav.restocking', icon: ['M20 12a8 8 0 00-14-5.3L4 9', 'M4 4v5h5', 'M4 12a8 8 0 0014 5.3L20 15', 'M20 20v-5h-5'] },
      { to: '/reports', label: 'nav.reports', icon: ['M6 3h8l4 4v14H6z', 'M14 3v4h4', 'M9 13h6', 'M9 17h6'] }
    ]

    return { t, navItems, mode, isRail, brandInitial, toggleLabel, toggleIcon }
  }
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  /* --shell-sidebar-width is set on .app (App.vue) and also drives the main column's
     margin, so the two cannot drift apart. */
  width: var(--shell-sidebar-width, var(--sidebar-width));
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-right: 1px solid var(--border);
  z-index: var(--z-sidebar);
  transition: width 0.2s ease, transform 0.2s ease, visibility 0s;
}

/* Drawer and tablet overlay are always full width, whatever the shell width is.
   The overlay floats over the content instead of pushing it: the content margin
   stays at the rail width, so opening it never reflows the page underneath. */
.sidebar.sidebar-mobile,
.sidebar.sidebar-overlay {
  width: var(--sidebar-width);
}

.sidebar.sidebar-overlay {
  box-shadow: var(--shadow-lg);
}

/* Visually hidden but still read by screen readers. Not display:none, which would
   remove the text from the accessibility tree and leave the rail items unnamed. */
.sr-only,
.sidebar.is-rail .nav-label {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  border: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}

.sidebar-brand {
  height: 64px;
  flex-shrink: 0;
  padding: 0 var(--space-4);
  display: flex;
  flex-direction: column;
  justify-content: center;
  border-bottom: 1px solid var(--border);
  min-width: 0;
}

.brand-mark {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-base);
  font-weight: 600;
  line-height: 1;
}

.sidebar.is-rail .sidebar-brand {
  align-items: center;
  padding: 0;
}

.brand-name {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text);
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* min-height: 0 lets the nav scroll on short screens instead of pushing the footer out */
.sidebar-nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-item {
  position: relative;
  width: 100%;
  border: 0;
  background: transparent;
  font-family: inherit;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  height: 40px;
  flex-shrink: 0;
  padding: 0 var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  text-decoration: none;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background: var(--surface-hover);
  color: var(--text);
}

.nav-item.active {
  background: var(--accent-soft);
  color: var(--accent);
}

/* 3px bar keeps the active state visible without relying on color alone */
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 var(--radius-full) var(--radius-full) 0;
  background: var(--accent);
}

.nav-item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.nav-icon {
  flex-shrink: 0;
}

/* Rail: icon centered; the label is visually hidden (see .sr-only above) */
.sidebar.is-rail .nav-item {
  justify-content: center;
  padding: 0;
}

.sidebar-toggle-row {
  flex-shrink: 0;
  padding: 0 var(--space-3) var(--space-3);
}

/* min-width: 0 is required for ellipsis to work on a flex child */
.nav-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* The footer is not an overflow container, so the upward dropdowns are not clipped */
.sidebar-footer {
  flex-shrink: 0;
  padding: var(--space-3);
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

/* Below 768px: off-canvas drawer, slid in by the menu button in App.vue */
.sidebar.sidebar-mobile {
  transform: translateX(-100%);
  visibility: hidden; /* keeps closed-drawer links out of the tab order */
  transition: transform 0.2s ease, visibility 0s linear 0.2s;
}

.sidebar.sidebar-mobile.sidebar-open {
  transform: translateX(0);
  visibility: visible;
  transition: transform 0.2s ease;
  box-shadow: var(--shadow-lg);
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar.sidebar-mobile,
  .sidebar.sidebar-mobile.sidebar-open {
    transition: none;
  }
}
</style>
