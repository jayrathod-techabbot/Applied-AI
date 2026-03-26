import { Trash2, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { IssueTypeBadge } from '@/components/shared/IssueTypeBadge'
import { SeverityBadge } from '@/components/shared/SeverityBadge'
import { StatusChip } from '@/components/shared/StatusChip'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { formatRelativeTime, truncate } from '@/lib/utils'
import type { StoredConversation } from '@/types/conversation'

interface Props {
  conversation: StoredConversation
  onClick: () => void
  onDelete: (id: string) => void
}

export function HistoryCard({ conversation: conv, onClick, onDelete }: Props) {
  return (
    <div
      className="group flex items-start gap-4 rounded-lg border bg-card p-4 hover:shadow-sm transition-all cursor-pointer"
      onClick={onClick}
    >
      <div className="h-9 w-9 rounded-md bg-muted flex items-center justify-center shrink-0 mt-0.5">
        <MessageSquare className="h-4 w-4 text-muted-foreground" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm text-foreground leading-snug line-clamp-2 mb-2">
          {truncate(conv.firstMessage, 120)}
        </p>
        <div className="flex items-center gap-1.5 flex-wrap">
          <IssueTypeBadge issueType={conv.issueType} />
          <SeverityBadge severity={conv.severity} />
          <StatusChip status={conv.status} />
          <span className="text-xs text-muted-foreground ml-auto">
            {conv.messageCount} messages · {formatRelativeTime(conv.updatedAt)}
          </span>
        </div>
      </div>

      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 opacity-0 group-hover:opacity-100 shrink-0 text-muted-foreground hover:text-destructive"
            onClick={(e) => e.stopPropagation()}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent onClick={(e) => e.stopPropagation()}>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete conversation?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently remove this conversation from your history.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => onDelete(conv.id)}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
