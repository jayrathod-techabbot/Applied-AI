import { MessageSquare, CheckCircle, AlertTriangle, Activity } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { KpiCard } from '@/components/dashboard/KpiCard'
import { IssueTypeChart } from '@/components/dashboard/IssueTypeChart'
import { SeverityBarChart } from '@/components/dashboard/SeverityBarChart'
import { ResolutionTrendChart } from '@/components/dashboard/ResolutionTrendChart'
import { useAnalytics } from '@/hooks/useAnalytics'

export function DashboardPage() {
  const {
    totalConversations, escalatedCount,
    resolutionRate, avgMessagesPerConversation,
    issueTypeDistribution, severityDistribution, resolutionTrend,
  } = useAnalytics()

  return (
    <ScrollArea className="h-full">
      <div className="p-6 space-y-6 max-w-6xl mx-auto">
        <div>
          <h2 className="text-lg font-semibold">Overview</h2>
          <p className="text-sm text-muted-foreground">Aggregated from locally stored conversations</p>
        </div>

        {/* KPI Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard label="Total Conversations" value={totalConversations} icon={MessageSquare} />
          <KpiCard
            label="Resolution Rate"
            value={resolutionRate}
            suffix="%"
            icon={CheckCircle}
            iconClassName="bg-emerald-100 dark:bg-emerald-900/30"
          />
          <KpiCard
            label="Escalated"
            value={escalatedCount}
            icon={AlertTriangle}
            iconClassName="bg-red-100 dark:bg-red-900/30"
          />
          <KpiCard
            label="Avg Messages"
            value={avgMessagesPerConversation}
            icon={Activity}
            iconClassName="bg-purple-100 dark:bg-purple-900/30"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <IssueTypeChart data={issueTypeDistribution} />
          <SeverityBarChart data={severityDistribution} />
        </div>

        {/* Trend */}
        <ResolutionTrendChart data={resolutionTrend} />
      </div>
    </ScrollArea>
  )
}
