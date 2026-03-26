import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { ErrorBoundary } from '@/components/shared/ErrorBoundary'
import { useSettingsStore } from '@/store/settingsStore'
import { useTheme } from '@/hooks/useTheme'
import { ROUTES } from '@/constants/routes'

const TITLES: Record<string, string> = {
  [ROUTES.CHAT]: 'Chat',
  [ROUTES.HISTORY]: 'Conversation History',
  [ROUTES.DASHBOARD]: 'Dashboard',
  [ROUTES.SETTINGS]: 'Settings',
}

export function AppShell() {
  // Apply theme to <html> element
  useTheme()

  const sidebarCollapsed = useSettingsStore((s) => s.sidebarCollapsed)
  const location = useLocation()
  const title = TITLES[location.pathname] ?? 'Customer Support Engine'

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar collapsed={sidebarCollapsed} />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopBar title={title} />
        <main className="flex-1 overflow-hidden">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}
