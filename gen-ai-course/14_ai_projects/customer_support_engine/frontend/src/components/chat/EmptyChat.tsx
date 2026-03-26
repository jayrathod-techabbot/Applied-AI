import { MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'

const SUGGESTIONS = [
  'I was charged twice for my subscription',
  'My password reset email never arrived',
  'How do I upgrade my plan?',
  'Our production API is returning 500 errors',
]

interface Props {
  onSuggest: (text: string) => void
}

export function EmptyChat({ onSuggest }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 px-4 text-center">
      <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center">
        <MessageSquare className="h-7 w-7 text-primary" />
      </div>
      <div>
        <h2 className="text-xl font-semibold">How can we help you?</h2>
        <p className="text-sm text-muted-foreground mt-1 max-w-xs">
          Ask about billing, technical issues, or general inquiries. Our AI will assist you.
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
        {SUGGESTIONS.map((s) => (
          <Button
            key={s}
            variant="outline"
            className="h-auto py-3 px-4 text-left justify-start text-sm leading-snug whitespace-normal"
            onClick={() => onSuggest(s)}
          >
            {s}
          </Button>
        ))}
      </div>
    </div>
  )
}
