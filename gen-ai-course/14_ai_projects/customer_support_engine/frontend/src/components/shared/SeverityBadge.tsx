import { cn } from '@/lib/utils'
import { SEVERITY_CONFIG } from '@/constants/severity'
import type { Severity } from '@/types/api'

interface Props {
  severity: Severity | null | undefined
  className?: string
}

export function SeverityBadge({ severity, className }: Props) {
  if (!severity) return null
  const config = SEVERITY_CONFIG[severity]
  return (
    <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', config.className, className)}>
      {config.label}
    </span>
  )
}
