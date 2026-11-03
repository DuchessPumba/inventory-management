import { ref, computed, getCurrentScope, onScopeDispose } from 'vue'

// Shared sidebar state (singleton pattern)
const STORAGE_KEY = 'sidebar-collapsed'
// Same breakpoints as the CSS (the .98 avoids a one-pixel gap on fractional widths)
const MOBILE_QUERY = '(max-width: 767.98px)'
const NARROW_QUERY = '(max-width: 1023.98px)'

// localStorage can throw (private mode, blocked storage), so every access is wrapped
// and the sidebar simply works without persistence.
const readPreference = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'true') return true
    if (saved === 'false') return false
  } catch (e) {
    // storage unavailable: fall through to the viewport default
  }
  return null
}

const writePreference = (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, String(value))
  } catch (e) {
    // ignore: the choice just will not survive a reload
  }
}

const hasMatchMedia = typeof window !== 'undefined' && typeof window.matchMedia === 'function'
const mobileQuery = hasMatchMedia ? window.matchMedia(MOBILE_QUERY) : null
const narrowQuery = hasMatchMedia ? window.matchMedia(NARROW_QUERY) : null

// Viewport flags, evaluated at load so the first render is already correct
const isMobileViewport = ref(mobileQuery ? mobileQuery.matches : false)
const isNarrow = ref(narrowQuery ? narrowQuery.matches : false) // below 1024px, includes mobile

// null = the user never chose; then the default depends on the viewport
const preference = ref(readPreference())

// Collapsed rail on desktop. Unless the user chose, it defaults to collapsed below 1024px
// and expanded above, and follows the viewport when resized. On tablet widths the rail is
// always shown and "expanded" is a temporary overlay owned by the caller, so this value
// only drives the desktop layout (and is ignored on mobile).
const collapsed = computed({
  get: () => (preference.value === null ? isNarrow.value : preference.value),
  set: (value) => {
    preference.value = Boolean(value)
    writePreference(preference.value)
  }
})

// mobile: < 768px (drawer), tablet: 768-1023px (rail + overlay), desktop: >= 1024px
const mode = computed(() => {
  if (isMobileViewport.value) return 'mobile'
  if (isNarrow.value) return 'tablet'
  return 'desktop'
})

const onMobileChange = (e) => { isMobileViewport.value = e.matches }
const onNarrowChange = (e) => { isNarrow.value = e.matches }

// Listeners are shared and reference counted: added by the first consumer,
// removed when the last consuming scope is disposed.
let subscribers = 0
const subscribe = () => {
  if (!mobileQuery || !narrowQuery) return
  if (subscribers === 0) {
    // Re-sync in case the viewport changed while nobody was listening
    isMobileViewport.value = mobileQuery.matches
    isNarrow.value = narrowQuery.matches
    mobileQuery.addEventListener('change', onMobileChange)
    narrowQuery.addEventListener('change', onNarrowChange)
  }
  subscribers++
}
const unsubscribe = () => {
  if (!mobileQuery || !narrowQuery) return
  subscribers = Math.max(0, subscribers - 1)
  if (subscribers === 0) {
    mobileQuery.removeEventListener('change', onMobileChange)
    narrowQuery.removeEventListener('change', onNarrowChange)
  }
}

export function useSidebar() {
  if (getCurrentScope()) {
    subscribe()
    onScopeDispose(unsubscribe)
  }

  const toggle = () => {
    collapsed.value = !collapsed.value
  }

  return {
    collapsed,
    toggle,
    mode,
    isMobile: computed(() => mode.value === 'mobile'),
    isTablet: computed(() => mode.value === 'tablet'),
    isDesktop: computed(() => mode.value === 'desktop')
  }
}
