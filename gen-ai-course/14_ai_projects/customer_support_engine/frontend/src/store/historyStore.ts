import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { StoredConversation } from '@/types/conversation'

interface HistoryState {
  conversations: StoredConversation[]
  upsertConversation: (conv: StoredConversation) => void
  deleteConversation: (id: string) => void
  clearAll: () => void
  getConversation: (id: string) => StoredConversation | undefined
}

export const useHistoryStore = create<HistoryState>()(
  persist(
    (set, get) => ({
      conversations: [],

      upsertConversation: (conv) =>
        set((s) => {
          const existing = s.conversations.findIndex((c) => c.id === conv.id)
          if (existing >= 0) {
            const updated = [...s.conversations]
            updated[existing] = conv
            return { conversations: updated }
          }
          return { conversations: [conv, ...s.conversations] }
        }),

      deleteConversation: (id) =>
        set((s) => ({ conversations: s.conversations.filter((c) => c.id !== id) })),

      clearAll: () => set({ conversations: [] }),

      getConversation: (id) => get().conversations.find((c) => c.id === id),
    }),
    { name: 'cse-history' }
  )
)
