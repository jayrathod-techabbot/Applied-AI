import { TrendingUp, TrendingDown } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

interface Props {
  label: string
  value: number | string
  suffix?: string
  delta?: number
  icon: LucideIcon
  iconClassName?: string
}

export function KpiCard({ label, value, suffix, delta, icon: Icon, iconClassName }: Props) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-3xl font-bold mt-1 tabular-nums">
              {value}
              {suffix && <span className="text-lg font-medium text-muted-foreground ml-1">{suffix}</span>}
            </p>
            {delta !== undefined && (
              <div className={cn('flex items-center gap-1 mt-1 text-xs', delta >= 0 ? 'text-emerald-600' : 'text-red-500')}>
                {delta >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                <span>{Math.abs(delta)}% vs last period</span>
              </div>
            )}
          </div>
          <div className={cn('h-10 w-10 rounded-lg flex items-center justify-center shrink-0', iconClassName ?? 'bg-primary/10')}>
            <Icon className="h-5 w-5 text-primary" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
