import { useState, useCallback, useRef } from 'react'
import { supportApi } from '@/lib/api'
import { useConversationStore } from '@/store/conversationStore'
import { useHistoryStore } from '@/store/historyStore'
import { useWebSocket } from './useWebSocket'
import { generateId } from '@/lib/utils'
import type { Message } from '@/types/conversation'

export function useConversation() {
  // Select stable action references individually — avoids creating a new object on every render
  const activeConversation = useConversationStore((s) => s.activeConversation)
  const wsStatus = useConversationStore((s) => s.wsStatus)
  const isTyping = useConversationStore((s) => s.isTyping)
  const error = useConversationStore((s) => s.error)
  const startConversation = useConversationStore((s) => s.startConversation)
  const appendMessage = useConversationStore((s) => s.appendMessage)
  const updateMeta = useConversationStore((s) => s.updateMeta)
  const setIsTyping = useConversationStore((s) => s.setIsTyping)
  const setError = useConversationStore((s) => s.setError)
  const reset = useConversationStore((s) => s.reset)
  const loadConversationAction = useConversationStore((s) => s.loadConversation)

  const upsertConversation = useHistoryStore((s) => s.upsertConversation)

  const [conversationId, setConversationId] = useState<string | null>(
    activeConversation?.id ?? null
  )

  const { send: wsSend } = useWebSocket(conversationId)
  const isFirstMessage = useRef(!activeConversation)

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return

      const userMsg: Message = {
        id: generateId(),
        role: 'user',
        content: text.trim(),
        timestamp: new Date().toISOString(),
      }

      // Read current state directly to avoid stale closure issues
      const currentConv = useConversationStore.getState().activeConversation

      if (isFirstMessage.current || !currentConv) {
        setIsTyping(true)
        setError(null)

        try {
          const res = await supportApi.start({ message: text.trim() })

          const assistantMsg: Message = {
            id: generateId(),
            role: 'assistant',
            content: res.reply,
            timestamp: new Date().toISOString(),
            issueType: res.issue_type,
            severity: res.severity,
            status: res.status,
          }

          startConversation(res.conversation_id, userMsg, assistantMsg, {
            issueType: res.issue_type,
            severity: res.severity,
            status: res.status,
          })

          setConversationId(res.conversation_id)
          isFirstMessage.current = false

          upsertConversation({
            id: res.conversation_id,
            firstMessage: text.trim(),
            issueType: res.issue_type,
            severity: res.severity,
            status: res.status,
            messageCount: 2,
            createdAt: userMsg.timestamp,
            updatedAt: assistantMsg.timestamp,
            messages: [userMsg, assistantMsg],
          })
        } catch (err) {
          setIsTyping(false)
          setError((err as { message?: string })?.message ?? 'Failed to start conversation')
        }
      } else {
        appendMessage(userMsg)
        setIsTyping(true)
        setError(null)

        const currentWsStatus = useConversationStore.getState().wsStatus
        if (currentWsStatus === 'open') {
          wsSend(text.trim())
        } else {
          // Fallback to REST if WebSocket isn't ready
          try {
            const res = await supportApi.start({
              message: text.trim(),
              conversation_id: currentConv.id,
            })
            setIsTyping(false)
            const assistantMsg: Message = {
              id: generateId(),
              role: 'assistant',
              content: res.reply,
              timestamp: new Date().toISOString(),
              issueType: res.issue_type,
              severity: res.severity,
              status: res.status,
            }
            appendMessage(assistantMsg)
            updateMeta({
              issueType: res.issue_type,
              severity: res.severity,
              status: res.status,
            })
          } catch (err) {
            setIsTyping(false)
            setError((err as { message?: string })?.message ?? 'Failed to send message')
          }
        }
      }
    },
    // Stable action refs from Zustand — these never change identity
    [startConversation, appendMessage, updateMeta, setIsTyping, setError, upsertConversation, wsSend]
  )

  const resetConversation = useCallback(() => {
    reset()
    setConversationId(null)
    isFirstMessage.current = true
  }, [reset])

  const loadConversation = useCallback(
    (conv: Parameters<typeof loadConversationAction>[0]) => {
      loadConversationAction(conv)
      setConversationId(conv.id)
      isFirstMessage.current = false
    },
    [loadConversationAction]
  )

  return {
    activeConversation,
    messages: activeConversation?.messages ?? [],
    wsStatus,
    isTyping,
    error,
    sendMessage,
    resetConversation,
    loadConversation,
  }
}
