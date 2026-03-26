import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Theme = 'light' | 'dark' | 'system'

interface SettingsState {
  apiBaseUrl: string
  theme: Theme
  sidebarCollapsed: boolean
  setApiBaseUrl: (url: string) => void
  setTheme: (theme: Theme) => void
  toggleSidebar: () => void
  setSidebarCollapsed: (v: boolean) => void
  reset: () => void
}

const DEFAULTS = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8003',
  theme: 'system' as Theme,
  sidebarCollapsed: false,
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...DEFAULTS,
      setApiBaseUrl: (url) => set({ apiBaseUrl: url }),
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),
      reset: () => set(DEFAULTS),
    }),
    { name: 'cse-settings' }
  )
)
