import { ConversationSidebar } from '@/components/chat/ConversationSidebar'
import { ChatPanel } from '@/components/chat/ChatPanel'

export function ChatPage() {
  return (
    <div className="flex h-full">
      <ConversationSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <ChatPanel />
      </div>
    </div>
  )
}
