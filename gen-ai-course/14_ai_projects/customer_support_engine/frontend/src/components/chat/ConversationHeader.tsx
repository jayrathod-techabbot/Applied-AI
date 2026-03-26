import { Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { IssueTypeBadge } from '@/components/shared/IssueTypeBadge'
import { SeverityBadge } from '@/components/shared/SeverityBadge'
import { StatusChip } from '@/components/shared/StatusChip'
import { Button } from '@/components/ui/button'
import type { IssueType, Severity, SupportStatus } from '@/types/api'

interface Props {
  conversationId: string
  issueType: IssueType | null | undefined
  severity: Severity | null | undefined
  status: SupportStatus | null | undefined
}

export function ConversationHeader({ conversationId, issueType, severity, status }: Props) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(conversationId)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex items-center gap-2 px-4 py-2 border-b bg-muted/30 flex-wrap">
      <IssueTypeBadge issueType={issueType} />
      <SeverityBadge severity={severity} />
      <StatusChip status={status} />
      <div className="ml-auto flex items-center gap-1.5 text-xs text-muted-foreground">
        <span className="font-mono">{conversationId.slice(0, 8)}…</span>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => void handleCopy()}>
          {copied ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
        </Button>
      </div>
    </div>
  )
}
