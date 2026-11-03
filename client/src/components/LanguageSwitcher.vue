<template>
  <div class="language-switcher" :class="{ compact }">
    <button
      class="language-button"
      :title="compact ? localeName : null"
      :aria-label="compact ? localeName : null"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        class="globe-icon"
      >
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M3 10H17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 7.5 5.5 7.5 10C7.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 12.5 5.5 12.5 10C12.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
      </svg>
      <span v-if="!compact" class="language-label">{{ localeName }}</span>
      <svg
        v-if="!compact"
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <div v-if="isDropdownOpen" class="dropdown-menu">
      <button
        v-for="locale in availableLocales"
        :key="locale"
        class="dropdown-item"
        :class="{ active: currentLocale === locale }"
        @mousedown.prevent="selectLanguage(locale)"
      >
        <span class="language-name">{{ getLanguageName(locale) }}</span>
        <svg
          v-if="currentLocale === locale"
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          class="check-icon"
        >
          <path d="M4 9L7.5 12.5L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from '../composables/useI18n'

defineProps({
  // Icon-only trigger for the collapsed sidebar rail
  compact: {
    type: Boolean,
    default: false
  }
})

const { currentLocale, setLocale, availableLocales, localeName } = useI18n()

const isDropdownOpen = ref(false)

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const handleBlur = () => {
  // Delay to allow mousedown events on dropdown items to fire first
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 200)
}

const selectLanguage = (locale) => {
  setLocale(locale)
  isDropdownOpen.value = false
}
</script>

<style scoped>
.language-switcher {
  position: relative;
}

.language-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.15s ease;
  font-family: inherit;
  font-size: var(--text-sm);
  color: var(--text);
  text-align: left;
}

.language-button:hover {
  background: var(--surface-hover);
}

.language-button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* Compact: 40px square icon button, centered in the rail */
.compact .language-button {
  width: 40px;
  height: 40px;
  padding: 0;
  justify-content: center;
  margin: 0 auto;
}

.globe-icon {
  color: var(--text-muted);
  flex-shrink: 0;
}

.language-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.chevron {
  color: var(--text-muted);
  transition: transform 0.2s ease;
  flex-shrink: 0;
  transform: rotate(180deg); /* points up while closed: the panel opens upward */
}

.chevron-open {
  transform: rotate(0deg);
}

/* Opens upward: this switcher sits at the bottom of the sidebar, so a
   downward panel would fall off the screen. Left-aligned, full trigger width. */
.dropdown-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  min-width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 1000;
  overflow: hidden;
}

/* Compact: the rail is only 72px wide, so open to the right of it, anchored to the
   bottom. 100% + 20px = 12px footer padding + 8px gap, measured from the 48px-wide wrapper. */
.compact .dropdown-menu {
  bottom: 0;
  left: calc(100% + 20px);
  min-width: 160px;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text);
}

.dropdown-item:hover {
  background: var(--surface-hover);
}

.dropdown-item.active {
  background: var(--accent-soft);
  color: var(--accent);
}

.language-name {
  flex: 1;
}

.check-icon {
  color: var(--accent);
  flex-shrink: 0;
}
</style>
