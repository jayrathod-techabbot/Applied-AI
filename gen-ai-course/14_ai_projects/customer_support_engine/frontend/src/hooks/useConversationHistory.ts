import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import { useHistoryStore } from '@/store/historyStore'
import type { IssueType, Severity, SupportStatus } from '@/types/api'

export interface HistoryFilter {
  issueTypes: IssueType[]
  severities: Severity[]
  statuses: SupportStatus[]
}

const EMPTY_FILTER: HistoryFilter = { issueTypes: [], severities: [], statuses: [] }

export function useConversationHistory() {
  const conversations = useHistoryStore((s) => s.conversations)
  const deleteConversation = useHistoryStore((s) => s.deleteConversation)
  const clearAll = useHistoryStore((s) => s.clearAll)
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [filters, setFilters] = useState<HistoryFilter>(EMPTY_FILTER)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => setDebouncedQuery(searchQuery), 300)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [searchQuery])

  const filteredConversations = useMemo(() => {
    let result = [...conversations].sort(
      (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    )

    if (debouncedQuery.trim()) {
      const q = debouncedQuery.toLowerCase()
      result = result.filter((c) => c.firstMessage.toLowerCase().includes(q))
    }

    if (filters.issueTypes.length > 0) {
      result = result.filter((c) => c.issueType && filters.issueTypes.includes(c.issueType))
    }
    if (filters.severities.length > 0) {
      result = result.filter((c) => c.severity && filters.severities.includes(c.severity))
    }
    if (filters.statuses.length > 0) {
      result = result.filter((c) => c.status && filters.statuses.includes(c.status))
    }

    return result
  }, [conversations, debouncedQuery, filters])

  const clearFilters = useCallback(() => {
    setSearchQuery('')
    setFilters(EMPTY_FILTER)
  }, [])

  return {
    conversations: filteredConversations,
    totalCount: conversations.length,
    searchQuery,
    setSearchQuery,
    filters,
    setFilters,
    clearFilters,
    deleteConversation,
    clearAll,
  }
}
