import { cn } from '@/lib/utils'
import { ISSUE_TYPE_CONFIG } from '@/constants/status'
import type { IssueType } from '@/types/api'

interface Props {
  issueType: IssueType | null | undefined
  className?: string
}

export function IssueTypeBadge({ issueType, className }: Props) {
  if (!issueType) return null
  const config = ISSUE_TYPE_CONFIG[issueType]
  return (
    <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', config.className, className)}>
      {config.label}
    </span>
  )
}
