import { useState, useEffect, useCallback } from 'react'
import { supportApi } from '@/lib/api'

export type ServiceStatus = 'ok' | 'degraded' | 'unreachable'

export function useHealthCheck() {
  const [isOnline, setIsOnline] = useState(true)
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus>('ok')
  const [lastChecked, setLastChecked] = useState<Date | null>(null)

  const check = useCallback(async () => {
    try {
      const res = await supportApi.health()
      setIsOnline(true)
      setServiceStatus(res.status === 'ok' ? 'ok' : 'degraded')
    } catch {
      setIsOnline(false)
      setServiceStatus('unreachable')
    } finally {
      setLastChecked(new Date())
    }
  }, [])

  useEffect(() => {
    void check()
    const interval = setInterval(() => void check(), 30_000)
    return () => clearInterval(interval)
  }, [check])

  return { isOnline, serviceStatus, lastChecked, check }
}
