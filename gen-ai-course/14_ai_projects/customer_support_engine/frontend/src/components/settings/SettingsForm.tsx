import { useState } from 'react'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useSettingsStore } from '@/store/settingsStore'
import { supportApi } from '@/lib/api'

export function SettingsForm() {
  const apiBaseUrl = useSettingsStore((s) => s.apiBaseUrl)
  const setApiBaseUrl = useSettingsStore((s) => s.setApiBaseUrl)
  const [localUrl, setLocalUrl] = useState(apiBaseUrl)
  const [testStatus, setTestStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [saved, setSaved] = useState(false)

  const isValid = /^https?:\/\/.+/.test(localUrl)

  const handleSave = () => {
    if (!isValid) return
    setApiBaseUrl(localUrl)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleTest = async () => {
    setTestStatus('loading')
    try {
      // Temporarily update the store so api.ts picks up the new URL
      setApiBaseUrl(localUrl)
      await supportApi.health()
      setTestStatus('ok')
    } catch {
      setTestStatus('error')
    } finally {
      setTimeout(() => setTestStatus('idle'), 3000)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Backend Connection</CardTitle>
        <CardDescription>Configure the URL of your Customer Support Engine backend.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="api-url">API Base URL</Label>
          <div className="flex gap-2">
            <Input
              id="api-url"
              value={localUrl}
              onChange={(e) => setLocalUrl(e.target.value)}
              placeholder="http://localhost:8003"
              className="flex-1 font-mono text-sm"
            />
            <Button
              variant="outline"
              onClick={() => void handleTest()}
              disabled={testStatus === 'loading' || !isValid}
              className="shrink-0"
            >
              {testStatus === 'loading' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : testStatus === 'ok' ? (
                <CheckCircle className="h-4 w-4 text-emerald-500" />
              ) : testStatus === 'error' ? (
                <XCircle className="h-4 w-4 text-destructive" />
              ) : (
                'Test'
              )}
            </Button>
          </div>
          {testStatus === 'ok' && <p className="text-xs text-emerald-600">Backend is healthy ✓</p>}
          {testStatus === 'error' && <p className="text-xs text-destructive">Could not reach backend</p>}
          {!isValid && localUrl && <p className="text-xs text-destructive">Enter a valid URL starting with http:// or https://</p>}
        </div>
        <Button onClick={handleSave} disabled={!isValid || localUrl === apiBaseUrl}>
          {saved ? '✓ Saved' : 'Save'}
        </Button>
      </CardContent>
    </Card>
  )
}
