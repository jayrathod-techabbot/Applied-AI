import { useMemo } from 'react'
import { useHistoryStore } from '@/store/historyStore'
import { formatDate } from '@/lib/utils'

export function useAnalytics() {
  const conversations = useHistoryStore((s) => s.conversations)

  return useMemo(() => {
    const total = conversations.length
    const resolved = conversations.filter((c) => c.status === 'resolved').length
    const escalated = conversations.filter((c) => c.status === 'escalated').length
    const resolutionRate = total > 0 ? Math.round((resolved / total) * 100) : 0
    const avgMessages =
      total > 0
        ? Math.round(conversations.reduce((sum, c) => sum + c.messageCount, 0) / total)
        : 0

    // Issue type distribution
    const issueTypeMap: Record<string, number> = {}
    conversations.forEach((c) => {
      const k = c.issueType ?? 'unknown'
      issueTypeMap[k] = (issueTypeMap[k] ?? 0) + 1
    })
    const issueTypeDistribution = Object.entries(issueTypeMap).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value,
    }))

    // Severity distribution
    const severityMap: Record<string, number> = {}
    conversations.forEach((c) => {
      const k = c.severity ?? 'unknown'
      severityMap[k] = (severityMap[k] ?? 0) + 1
    })
    const severityDistribution = ['low', 'medium', 'high', 'critical'].map((s) => ({
      severity: s.charAt(0).toUpperCase() + s.slice(1),
      count: severityMap[s] ?? 0,
    }))

    // Resolution trend — last 14 days
    const now = Date.now()
    const trendMap: Record<string, { resolved: number; escalated: number }> = {}
    for (let i = 13; i >= 0; i--) {
      const d = new Date(now - i * 86_400_000)
      const key = formatDate(d.toISOString())
      trendMap[key] = { resolved: 0, escalated: 0 }
    }
    conversations.forEach((c) => {
      const key = formatDate(c.updatedAt)
      if (key in trendMap) {
        if (c.status === 'resolved') trendMap[key]!.resolved++
        if (c.status === 'escalated') trendMap[key]!.escalated++
      }
    })
    const resolutionTrend = Object.entries(trendMap).map(([date, counts]) => ({
      date,
      ...counts,
    }))

    return {
      totalConversations: total,
      resolvedCount: resolved,
      escalatedCount: escalated,
      resolutionRate,
      avgMessagesPerConversation: avgMessages,
      issueTypeDistribution,
      severityDistribution,
      resolutionTrend,
    }
  }, [conversations])
}
