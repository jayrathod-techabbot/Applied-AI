import { cn } from '@/lib/utils'
import { STATUS_CONFIG } from '@/constants/status'
import type { SupportStatus } from '@/types/api'

interface Props {
  status: SupportStatus | null | undefined
  className?: string
}

export function StatusChip({ status, className }: Props) {
  if (!status) return null
  const config = STATUS_CONFIG[status]
  return (
    <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', config.className, className)}>
      {config.label}
    </span>
  )
}
