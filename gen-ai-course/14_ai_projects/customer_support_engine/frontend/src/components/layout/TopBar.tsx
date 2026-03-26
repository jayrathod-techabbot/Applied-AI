import { PanelLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/settings/ThemeToggle'
import { ConnectionStatus } from '@/components/shared/ConnectionStatus'
import { useSettingsStore } from '@/store/settingsStore'
import { useConversationStore } from '@/store/conversationStore'
import { useHealthCheck } from '@/hooks/useHealthCheck'

interface Props {
  title: string
}

export function TopBar({ title }: Props) {
  const toggleSidebar = useSettingsStore((s) => s.toggleSidebar)
  const wsStatus = useConversationStore((s) => s.wsStatus)
  const { serviceStatus } = useHealthCheck()

  return (
    <header className="flex h-14 items-center gap-3 border-b px-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
      <Button variant="ghost" size="icon" onClick={toggleSidebar} aria-label="Toggle sidebar">
        <PanelLeft className="h-4 w-4" />
      </Button>
      <h1 className="text-sm font-semibold flex-1">{title}</h1>
      <ConnectionStatus serviceStatus={serviceStatus} wsStatus={wsStatus} />
      <ThemeToggle />
    </header>
  )
}
