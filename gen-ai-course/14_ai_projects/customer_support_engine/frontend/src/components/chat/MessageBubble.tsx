import ReactMarkdown from 'react-markdown'
import { AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatRelativeTime } from '@/lib/utils'
import type { Message } from '@/types/conversation'

interface Props {
  message: Message
  onRetry?: () => void
}

export function MessageBubble({ message, onRetry }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex gap-3 px-4 py-2', isUser ? 'flex-row-reverse' : 'flex-row')}>
      {/* Avatar */}
      <div
        className={cn(
          'h-8 w-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 mt-1',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
        )}
      >
        {isUser ? 'U' : 'AI'}
      </div>

      {/* Bubble */}
      <div className={cn('flex flex-col gap-1 max-w-[80%] min-w-0', isUser && 'items-end')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-3 text-sm leading-relaxed break-words',
            isUser
              ? 'bg-primary text-primary-foreground rounded-tr-sm'
              : message.isError
              ? 'bg-destructive/10 text-destructive border border-destructive/20 rounded-tl-sm'
              : 'bg-muted text-foreground rounded-tl-sm'
          )}
        >
          {message.isError && (
            <div className="flex items-center gap-1.5 mb-1 text-xs font-medium">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>Error</span>
            </div>
          )}
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
          {message.isError && onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 text-xs underline underline-offset-2 opacity-70 hover:opacity-100"
            >
              Retry
            </button>
          )}
        </div>
        <span className="text-xs text-muted-foreground px-1">
          {formatRelativeTime(message.timestamp)}
        </span>
      </div>
    </div>
  )
}
