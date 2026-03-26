import { useState, useRef, type KeyboardEvent } from 'react'
import { Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

interface Props {
  onSend: (text: string) => void
  disabled?: boolean
  error?: string | null
}

const MAX_CHARS = 2000

export function ChatInputBar({ onSend, disabled, error }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    // Reset height
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const v = e.target.value
    if (v.length > MAX_CHARS) return
    setValue(v)
    // Auto-resize
    const el = e.target
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }

  const remaining = MAX_CHARS - value.length

  return (
    <div className="border-t bg-background p-4">
      {error && (
        <p className="text-xs text-destructive mb-2 px-1">{error}</p>
      )}
      <div className="flex items-end gap-2 rounded-xl border bg-background shadow-sm focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-1 px-3 py-2">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message… (Ctrl+Enter to send)"
          disabled={disabled}
          rows={1}
          className={cn(
            'border-0 p-0 shadow-none focus-visible:ring-0 resize-none bg-transparent min-h-[24px] max-h-[200px]',
            disabled && 'opacity-60'
          )}
        />
        <div className="flex items-center gap-2 shrink-0 pb-0.5">
          {value.length > MAX_CHARS * 0.8 && (
            <span className={cn('text-xs', remaining < 50 ? 'text-destructive' : 'text-muted-foreground')}>
              {remaining}
            </span>
          )}
          <Button
            size="icon"
            onClick={handleSubmit}
            disabled={disabled || !value.trim()}
            className="h-8 w-8 shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <p className="text-xs text-muted-foreground mt-1 px-1">Press Ctrl+Enter to send</p>
    </div>
  )
}
