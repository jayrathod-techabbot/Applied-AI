import { cn } from '@/lib/utils'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { ServiceStatus } from '@/hooks/useHealthCheck'
import type { WsStatus } from '@/types/conversation'

interface Props {
  serviceStatus: ServiceStatus
  wsStatus: WsStatus
}

export function ConnectionStatus({ serviceStatus, wsStatus }: Props) {
  const isOnline = serviceStatus === 'ok'
  const isWsOpen = wsStatus === 'open'
  const isReconnecting = wsStatus === 'reconnecting'

  const dotClass = cn(
    'h-2 w-2 rounded-full',
    isOnline && isWsOpen ? 'bg-emerald-500' :
    isReconnecting ? 'bg-amber-500 animate-pulse' :
    !isOnline ? 'bg-red-500' : 'bg-amber-400'
  )

  const label = isOnline && isWsOpen
    ? 'Connected'
    : isReconnecting
    ? 'Reconnecting…'
    : !isOnline
    ? 'Backend unreachable'
    : 'WebSocket idle'

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="flex items-center gap-1.5 cursor-default">
          <span className={dotClass} />
          <span className="text-xs text-muted-foreground hidden sm:inline">{label}</span>
        </div>
      </TooltipTrigger>
      <TooltipContent side="bottom">
        <p>{label}</p>
      </TooltipContent>
    </Tooltip>
  )
}
