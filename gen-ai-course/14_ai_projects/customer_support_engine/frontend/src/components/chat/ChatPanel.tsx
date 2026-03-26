import { ConversationHeader } from './ConversationHeader'
import { MessageList } from './MessageList'
import { ChatInputBar } from './ChatInputBar'
import { EmptyChat } from './EmptyChat'
import { useConversation } from '@/hooks/useConversation'

export function ChatPanel() {
  const { activeConversation, messages, isTyping, error, sendMessage } = useConversation()

  return (
    <div className="flex flex-col h-full">
      {activeConversation && (
        <ConversationHeader
          conversationId={activeConversation.id}
          issueType={activeConversation.issueType}
          severity={activeConversation.severity}
          status={activeConversation.status}
        />
      )}

      {!activeConversation ? (
        <div className="flex-1">
          <EmptyChat onSuggest={(text) => void sendMessage(text)} />
        </div>
      ) : (
        <MessageList
          messages={messages}
          isTyping={isTyping}
        />
      )}

      <ChatInputBar
        onSend={(text) => void sendMessage(text)}
        disabled={isTyping}
        error={error}
      />
    </div>
  )
}
