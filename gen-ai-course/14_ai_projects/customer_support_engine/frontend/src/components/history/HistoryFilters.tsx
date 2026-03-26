import { Filter, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuCheckboxItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { HistoryFilter } from '@/hooks/useConversationHistory'
import type { IssueType, Severity, SupportStatus } from '@/types/api'

interface Props {
  filters: HistoryFilter
  onChange: (f: HistoryFilter) => void
  onClear: () => void
}

const ISSUE_TYPES: IssueType[] = ['billing', 'technical', 'general']
const SEVERITIES: Severity[] = ['low', 'medium', 'high', 'critical']
const STATUSES: SupportStatus[] = ['open', 'resolving', 'resolved', 'escalated']

function toggle<T>(arr: T[], item: T): T[] {
  return arr.includes(item) ? arr.filter((x) => x !== item) : [...arr, item]
}

const hasFilters = (f: HistoryFilter) =>
  f.issueTypes.length > 0 || f.severities.length > 0 || f.statuses.length > 0

export function HistoryFilters({ filters, onChange, onClear }: Props) {
  return (
    <div className="flex items-center gap-2">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="gap-2">
            <Filter className="h-3.5 w-3.5" />
            Filters
            {hasFilters(filters) && (
              <span className="ml-1 h-4 w-4 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center">
                {filters.issueTypes.length + filters.severities.length + filters.statuses.length}
              </span>
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-48" align="end">
          <DropdownMenuLabel>Issue Type</DropdownMenuLabel>
          {ISSUE_TYPES.map((t) => (
            <DropdownMenuCheckboxItem
              key={t}
              checked={filters.issueTypes.includes(t)}
              onCheckedChange={() => onChange({ ...filters, issueTypes: toggle(filters.issueTypes, t) })}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </DropdownMenuCheckboxItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuLabel>Severity</DropdownMenuLabel>
          {SEVERITIES.map((s) => (
            <DropdownMenuCheckboxItem
              key={s}
              checked={filters.severities.includes(s)}
              onCheckedChange={() => onChange({ ...filters, severities: toggle(filters.severities, s) })}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </DropdownMenuCheckboxItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuLabel>Status</DropdownMenuLabel>
          {STATUSES.map((s) => (
            <DropdownMenuCheckboxItem
              key={s}
              checked={filters.statuses.includes(s)}
              onCheckedChange={() => onChange({ ...filters, statuses: toggle(filters.statuses, s) })}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </DropdownMenuCheckboxItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {hasFilters(filters) && (
        <Button variant="ghost" size="sm" onClick={onClear} className="gap-1 text-muted-foreground">
          <X className="h-3.5 w-3.5" /> Clear
        </Button>
      )}
    </div>
  )
}
